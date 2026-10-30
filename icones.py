"""Icones dos jogos guardados no computador (pasta 'icones' ao lado do app).

Ordem de busca de um icone ainda nao baixado:
  1. URL do icone na pagina do prosperopatches (PS5) / orbispatches (PS4);
  2. reserva: imagem da PS Store (API "chihiro"), montada pelo Content ID, com tempo de espera curto.
Depois de baixado, o icone e servido do disco (instantaneo e sem internet).
"""

import threading
import time
import urllib.error
import urllib.request

import ftp_ps5
from consulta_ps5 import USER_AGENT, normalizar

PASTA_ICONES = ftp_ps5.PASTA_APP / "icones"
TIMEOUT_SITE = 6
TIMEOUT_LOJA = 8          # a PS Store costuma levar 5-7 s na primeira resposta
NOVA_TENTATIVA_S = 300    # icone que falhou e tentado de novo apos 5 minutos
TAMANHO_MAX = 2 * 1024 * 1024
TIPOS = {"image/webp": ".webp", "image/jpeg": ".jpg", "image/png": ".png"}

# Prefixo do Content ID (regiao do publisher) -> pais/idioma da PS Store.
LOJAS = {"U": ("US", "en"), "E": ("GB", "en"), "J": ("JP", "ja"), "H": ("HK", "en"), "K": ("KR", "ko")}
URL_LOJA = "https://store.playstation.com/store/api/chihiro/00_09_000/container/{pais}/{idioma}/999/{content_id}/image?w=256"

_sem_icone: dict[str, float] = {}  # codigo -> hora da falha (nao tenta de novo a cada render da tela)
_travas: dict[str, threading.Lock] = {}
_trava_geral = threading.Lock()


def _arquivo_local(codigo: str):
    for extensao in TIPOS.values():
        caminho = PASTA_ICONES / f"{codigo}{extensao}"
        if caminho.exists():
            return caminho
    return None


def _tipo_pelo_conteudo(dados: bytes) -> str:
    """O CDN dos sites nao envia Content-Type: identifica a imagem pelos primeiros bytes."""
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "image/webp"
    if dados[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if dados[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return ""


def _baixar_imagem(url: str, timeout: int, tentativas: int = 2) -> tuple[bytes, str] | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = resp.read(TAMANHO_MAX + 1)
            break
        except urllib.error.HTTPError:
            return None  # 404 etc.: nao adianta repetir
        except (urllib.error.URLError, TimeoutError, OSError):
            if tentativa == tentativas - 1:
                return None  # a rede as vezes trava numa conexao e na seguinte responde rapido
    tipo = _tipo_pelo_conteudo(dados)
    if not tipo or len(dados) > TAMANHO_MAX:
        return None
    return dados, tipo


def url_loja(content_id: str) -> str:
    loja = LOJAS.get(content_id[:1].upper())
    if not loja or "-" not in content_id:
        return ""
    return URL_LOJA.format(pais=loja[0], idioma=loja[1], content_id=content_id)


def obter(codigo: str, buscar_info) -> tuple[bytes, str] | None:
    """Devolve (bytes, content-type) do icone. buscar_info(codigo) -> dict com 'icone' e 'content_id'."""
    codigo = normalizar(codigo)
    if len(codigo) != 9 or not codigo.isalnum():
        return None
    with _trava_geral:
        trava = _travas.setdefault(codigo, threading.Lock())
    with trava:  # evita baixar o mesmo icone duas vezes ao mesmo tempo
        local = _arquivo_local(codigo)
        if local:
            tipo = next(t for t, e in TIPOS.items() if e == local.suffix)
            return local.read_bytes(), tipo
        if time.time() - _sem_icone.get(codigo, 0) < NOVA_TENTATIVA_S:
            return None

        info = buscar_info(codigo) or {}
        imagem = None
        if info.get("icone"):
            imagem = _baixar_imagem(info["icone"], TIMEOUT_SITE)
        if not imagem and url_loja(info.get("content_id", "")):
            imagem = _baixar_imagem(url_loja(info["content_id"]), TIMEOUT_LOJA)
        if not imagem:
            _sem_icone[codigo] = time.time()
            return None
        _sem_icone.pop(codigo, None)

        dados, tipo = imagem
        PASTA_ICONES.mkdir(exist_ok=True)
        (PASTA_ICONES / f"{codigo}{TIPOS[tipo]}").write_bytes(dados)
        return dados, tipo


def quantidade() -> int:
    return sum(1 for _ in PASTA_ICONES.glob("*.*")) if PASTA_ICONES.exists() else 0
