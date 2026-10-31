"""Game Library Renamer - interface grafica local (janela propria com WebView2) para consultar Title IDs de PS4/PS5
e renomear arquivos/pastas no PS5 via FTP/SFTP.

Uso:
    python app_ps5.py            (abre a janela do app; sem WebView2, abre no navegador padrao)
    python app_ps5.py --porta 9000 --sem-navegador

O servidor escuta somente em 127.0.0.1 (nao fica acessivel na rede).
Configuracao (FTP do PS5 e pastas a escanear): GameLibraryRenamer.ini, na pasta do app.
"""

import argparse
import json
import re
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import base_titulos
import foco
import ftp_ps5
import icones
import janela
from consulta_ps5 import CAMPOS, SITES, consultar, normalizar

PAGINA = ftp_ps5.PASTA_RECURSOS / "app_ps5.html"
ARQUIVO_CACHE = ftp_ps5.PASTA_APP / "cache_consultas.json"
VALIDADE_NAO_ENCONTRADO = 7 * 24 * 3600  # codigo nao encontrado e consultado de novo apos 7 dias
_trava_cache = threading.Lock()


def _carregar_cache() -> dict[str, dict]:
    try:
        dados = json.loads(ARQUIVO_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    # Descarta entradas gravadas por versoes antigas (sem algum campo atual, ex.: icone).
    return {k: v for k, v in dados.items() if isinstance(v, dict) and all(c in v for c in CAMPOS)}


_cache_consultas: dict[str, dict] = _carregar_cache()


def _gravar_cache() -> None:
    temporario = ARQUIVO_CACHE.with_suffix(".tmp")
    temporario.write_text(json.dumps(_cache_consultas, ensure_ascii=False, indent=1), encoding="utf-8")
    temporario.replace(ARQUIVO_CACHE)


_travas_codigo: dict[str, threading.Lock] = {}


def consultar_com_cache(codigo: str) -> dict:
    """Consulta guardando o resultado em cache_consultas.json (vale entre execucoes do app)."""
    chave = normalizar(codigo)
    with _trava_cache:
        trava = _travas_codigo.setdefault(chave, threading.Lock())
    with trava:  # a lista e os icones pedem o mesmo codigo ao mesmo tempo: consulta o site uma vez so
        with _trava_cache:
            guardado = _cache_consultas.get(chave)
            if guardado and (guardado["status"] == "ok"
                             or time.time() - guardado.get("_quando", 0) < VALIDADE_NAO_ENCONTRADO):
                return {**guardado, "cache": True}
        resultado = consultar(codigo)
        if resultado["status"] in ("ok", "nao encontrado"):
            with _trava_cache:
                _cache_consultas[chave] = {**resultado, "_quando": time.time()}
                _gravar_cache()
        return {**resultado, "cache": False}


def info_icone(codigo: str) -> dict:
    """URL do icone no site e Content ID (do site ou, se o site nao tiver, da base local)."""
    site = consultar_com_cache(codigo)
    base = base_titulos.consultar_base(codigo) or {}
    return {"icone": site.get("icone", ""), "content_id": site.get("content_id") or base.get("content_id", "")}


def limpar_cache() -> int:
    with _trava_cache:
        qtd = len(_cache_consultas)
        _cache_consultas.clear()
        ARQUIVO_CACHE.unlink(missing_ok=True)
    return qtd


_conexao = ftp_ps5.normalizar_conexao

# ---------------------------------------------------------------- vida da tela
# Com a janela propria, fechar a janela encerra o app. Na reserva (tela no navegador padrao), a
# pagina avisa a cada 5s que esta aberta (/api/ping) e, ao fechar, manda /api/fechou.
# Assim o app nunca fica rodando escondido sem tela (o que prendia os arquivos na atualizacao).
ESPERA_FECHOU_S = 6          # apos /api/fechou, encerra se nenhuma tela der sinal nesse tempo
SEM_SINAL_S = 180            # rede de seguranca: nenhum sinal por 3 min (tela minimizada pinga menos)
_vida = {"ultimo_ping": time.time(), "fechou_em": 0.0}


def _vigiar_tela(servidor) -> None:
    while True:
        time.sleep(2)
        agora = time.time()
        fechou = _vida["fechou_em"]
        if fechou and agora - fechou > ESPERA_FECHOU_S and _vida["ultimo_ping"] < fechou:
            break  # a tela fechou e nenhuma outra tela do app deu sinal depois disso
        if agora - _vida["ultimo_ping"] > SEM_SINAL_S:
            break
    servidor.shutdown()


class Handler(BaseHTTPRequestHandler):
    def _responder(self, status: int, corpo: bytes, tipo: str, cache: str = "no-store") -> None:
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, dados, status: int = 200) -> None:
        self._responder(status, json.dumps(dados, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

    def _origem_local(self) -> bool:
        """Bloqueia chamadas de outros sites (DNS rebinding / CSRF): so aceita host local."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return host in ("127.0.0.1", "localhost")

    def do_GET(self) -> None:
        try:
            self._do_get()
        except Exception as erro:  # ex.: INI com erro de sintaxe; a tela mostra a mensagem
            self._json({"ok": False, "erro": str(erro).strip() or erro.__class__.__name__,
                        "chave": getattr(erro, "chave", ""), "params": getattr(erro, "params", {})}, 500)

    def _do_get(self) -> None:
        if not self._origem_local():
            self._responder(403, b"Proibido", "text/plain; charset=utf-8")
            return
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self._responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
        elif url.path == "/api/consulta":
            # Base local primeiro (instantaneo); se nao achar, consulta o site.
            codigo = urllib.parse.parse_qs(url.query).get("codigo", [""])[0]
            local = base_titulos.consultar_base(codigo)
            if local:
                self._json({**local, "fonte": "base", "cache": True})
            else:
                self._json({**consultar_com_cache(codigo), "fonte": "site"})
        elif url.path == "/api/ping":
            # ?consulta=1 so le o estado (diagnostico), sem contar como sinal da tela.
            if "consulta=1" not in url.query:
                _vida["ultimo_ping"] = time.time()
            self._json({"ok": True, "fechou_em": _vida["fechou_em"], "ultimo_ping": _vida["ultimo_ping"]})
        elif url.path == "/favicon.ico":
            favicon = next((p for p in (ftp_ps5.PASTA_RECURSOS / "icone.ico", ftp_ps5.PASTA_APP / "instalador" / "icone.ico")
                            if p.exists()), None)
            if favicon:
                self._responder(200, favicon.read_bytes(), "image/x-icon", "max-age=86400")
            else:
                self._responder(404, b"", "text/plain")
        elif url.path.startswith("/icone/"):
            # Icone guardado no computador; baixa na primeira vez (site e, de reserva, PS Store).
            imagem = icones.obter(url.path.rsplit("/", 1)[-1], info_icone)
            if imagem:
                self._responder(200, imagem[0], imagem[1], "max-age=604800")
            else:
                self._responder(404, b"Sem icone", "text/plain; charset=utf-8")
        elif url.path == "/api/detalhes":
            # Icone e nome do publisher (a base local nao tem): sempre do site, com cache.
            codigo = urllib.parse.parse_qs(url.query).get("codigo", [""])[0]
            r = consultar_com_cache(codigo)
            self._json({"title_id": r["title_id"], "icone": r["icone"], "publisher": r["publisher"],
                        "status": r["status"], "cache": r["cache"]})
        elif url.path == "/api/config":
            self._json({**ftp_ps5.ler_config(), "cache_qtd": len(_cache_consultas), "icones_qtd": icones.quantidade(), "base": base_titulos.estado()})
        else:
            self._responder(404, b"Nao encontrado", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        # Exigir JSON obriga o navegador a fazer preflight CORS em chamadas de outros sites,
        # que este servidor nao autoriza.
        tipo = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if not self._origem_local() or tipo != "application/json":
            self._responder(403, b"Proibido", "text/plain; charset=utf-8")
            return
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
            dados = json.loads(self.rfile.read(tamanho) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json({"ok": False, "erro": "requisicao invalida"}, 400)
            return

        rota = urllib.parse.urlparse(self.path).path
        try:
            if rota == "/api/config":
                ftp_ps5.gravar_config(_conexao(dados))
                self._json({"ok": True, "config": ftp_ps5.ler_config()})
            elif rota == "/api/escanear":
                pastas = ftp_ps5.ler_config()["pastas"]
                if not pastas:
                    raise ftp_ps5.ErroApp("sem_pastas", f"nenhuma pasta configurada em {ftp_ps5.ARQUIVO_INI}", ini=str(ftp_ps5.ARQUIVO_INI))
                self._json({"ok": True, "pastas": pastas, **ftp_ps5.escanear(_conexao(dados), pastas)})
            elif rota == "/api/pastas":
                # Lista de pastas editada pela tela: grava no INI na ordem recebida.
                pastas = [str(p).strip() for p in dados.get("pastas", []) if str(p).strip()]
                if any(not p.startswith("/") for p in pastas):
                    raise ftp_ps5.ErroApp("pasta_invalida", "o caminho deve comecar com /")
                pastas = list(dict.fromkeys(pastas))  # sem repetidas
                ftp_ps5.gravar_config(pastas={f"folder{i}": p for i, p in enumerate(pastas, 1)})
                self._json({"ok": True, "pastas": ftp_ps5.ler_config()["pastas"]})
            elif rota == "/api/idioma":
                idioma = str(dados.get("idioma", ""))
                if idioma not in ftp_ps5.IDIOMAS:
                    raise ValueError("idioma invalido")
                ftp_ps5.gravar_config(idioma=idioma)
                self._json({"ok": True})
            elif rota == "/api/fechou":
                _vida["fechou_em"] = time.time()
                self._json({"ok": True})
            elif rota == "/api/sair":
                self._json({"ok": True})
                # Encerra depois de responder (shutdown precisa rodar fora da thread do pedido).
                threading.Thread(target=_encerrar, args=(self.server,), daemon=True).start()
            elif rota == "/api/mostrar":
                janela.trazer_para_frente()  # outra copia do app foi aberta: mostra esta janela
                self._json({"ok": True})
            elif rota == "/api/abrir-link":
                webbrowser.open(link_externo(dados))  # navegador padrao do usuario, fora da janela do app
                foco.trazer_navegador_para_frente()   # sem isso, com o navegador minimizado ele so pisca
                self._json({"ok": True})
            elif rota == "/api/editar-ini":
                # Abre o INI no Bloco de Notas do Windows (sempre o arquivo do app, nunca um caminho vindo da tela).
                ftp_ps5.ler_config()  # garante que o arquivo existe
                subprocess.Popen(["notepad.exe", str(ftp_ps5.ARQUIVO_INI)])
                foco.trazer_janela_com_titulo(ftp_ps5.ARQUIVO_INI.name)
                self._json({"ok": True})
            elif rota == "/api/limpar-cache":
                self._json({"ok": True, "removidos": limpar_cache()})
            elif rota == "/api/renomear":
                ftp_ps5.renomear(_conexao(dados), str(dados.get("pasta", "")),
                                 str(dados.get("de", "")), str(dados.get("para", "")))
                self._json({"ok": True})
            else:
                self._responder(404, b"Nao encontrado", "text/plain; charset=utf-8")
        except Exception as erro:  # qualquer falha (FTP, SFTP, rede) volta como mensagem para a tela
            self._json({"ok": False, "erro": str(erro).strip() or erro.__class__.__name__,
                        "chave": getattr(erro, "chave", ""), "params": getattr(erro, "params", {})})

    def log_message(self, formato, *args) -> None:
        pass  # silencia o log de cada requisicao no console


URL_FTPSRV = "https://github.com/ps5-payload-dev/ftpsrv"
LOCAL_LOJA = {"pt-BR": "pt-br", "en": "en-us", "es": "es-es"}


def link_externo(dados: dict) -> str:
    """Monta o link aqui (e nao na tela): o app so abre os sites conhecidos."""
    tipo = str(dados.get("tipo", ""))
    if tipo == "ftpsrv":
        return URL_FTPSRV
    if tipo == "loja":
        conceito = str(dados.get("concept_id", "")).strip()
        if not conceito.isdigit():
            raise ValueError("jogo sem pagina na PlayStation Store")
        local = LOCAL_LOJA.get(str(dados.get("idioma", "")), "pt-br")
        return f"https://store.playstation.com/{local}/concept/{conceito}"
    if tipo == "patches":
        # Pagina do jogo no prosperopatches (PS5) / orbispatches (PS4), pelo Title ID.
        codigo = normalizar(str(dados.get("codigo", "")))
        if not re.fullmatch(r"[A-Z]{4}\d{5}", codigo):
            raise ValueError("codigo invalido")
        return SITES["PS4" if codigo.startswith("CUSA") else "PS5"] + codigo
    if tipo == "youtube":
        nome = str(dados.get("nome", "")).strip()[:150]
        if not nome:
            raise ValueError("jogo sem nome")
        return "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": f"{nome} gameplay"})
    raise ValueError("link desconhecido")


class ServidorExclusivo(ThreadingHTTPServer):
    """No Windows, o SO_REUSEADDR padrao deixa duas copias do app ouvirem a mesma porta
    (e o navegador cai na copia antiga). Aqui a porta e de uso exclusivo."""

    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _encerrar(servidor) -> None:
    janela.fechar()  # fecha a janela junto (o main encerra quando ela fecha)
    servidor.shutdown()


def _mostrar_copia_aberta(endereco: str) -> None:
    """Pede para a copia que ja esta rodando mostrar a janela dela; sem resposta, abre no navegador."""
    pedido = urllib.request.Request(endereco + "/api/mostrar", data=b"{}", method="POST",
                                    headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(pedido, timeout=3).read()
    except OSError:
        janela.abrir_navegador(endereco)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interface local de consulta de Title IDs PS4/PS5")
    parser.add_argument("--porta", type=int, default=8765)
    parser.add_argument("--sem-navegador", action="store_true", help="nao abre o navegador automaticamente")
    args = parser.parse_args()

    endereco = f"http://127.0.0.1:{args.porta}"
    try:
        servidor = ServidorExclusivo(("127.0.0.1", args.porta), Handler)
    except OSError:
        # Porta ocupada: o app ja esta aberto. Nao abre uma segunda copia, so mostra a janela.
        print(f"O Game Library Renamer ja esta aberto em {endereco} - mostrando a janela dele.")
        if not args.sem_navegador:
            _mostrar_copia_aberta(endereco)
        return

    try:
        ftp_ps5.ler_config()  # cria o GameLibraryRenamer.ini modelo na primeira execucao
    except ftp_ps5.ErroApp as erro:
        print(f"Aviso: {erro}")  # INI com erro: o app abre assim mesmo e mostra o erro na tela
    base_titulos.atualizar_em_segundo_plano()  # carrega/baixa a base local de titulos
    print(f"Game Library Renamer {ftp_ps5.VERSAO} rodando em {endereco}  (feche a janela, Ctrl+C ou botao Sair para encerrar)")
    print(f"Configuracao: {ftp_ps5.ARQUIVO_INI}")
    rodando = threading.Thread(target=servidor.serve_forever, daemon=True)
    rodando.start()
    try:
        # Janela propria (pywebview): so volta quando a janela fecha (ou pelo botao Sair).
        if args.sem_navegador or not janela.mostrar(endereco):
            if not args.sem_navegador:
                # Reserva: navegador padrao; encerra quando a tela some (aba fechada, sem sinal...).
                janela.abrir_navegador(endereco)
                threading.Thread(target=_vigiar_tela, args=(servidor,), daemon=True).start()
            while rodando.is_alive():
                rodando.join(0.5)
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        servidor.shutdown()
        servidor.server_close()


if __name__ == "__main__":
    main()
