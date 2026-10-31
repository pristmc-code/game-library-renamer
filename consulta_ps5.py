"""Consulta Title IDs de PS5 (ex.: PPSA08329) e PS4 (ex.: CUSA10249).

PS5 -> prosperopatches.com | PS4 -> orbispatches.com (mesmo layout de pagina).
Codigos CUSA vao ao site de PS4; os demais (PPSA e codigos de disco) ao site de PS5.

Uso:
    python consulta_ps5.py PPSA08329
    python consulta_ps5.py PPSA08329 CUSA10249 PPSA01532
    python consulta_ps5.py -a codigos.txt            (um codigo por linha)
    python consulta_ps5.py -a codigos.txt -o resultado.csv
    python consulta_ps5.py -a codigos.txt -l nomes.txt   (so as linhas para renomear)

Retorna: Title ID, plataforma, nome do jogo, nome para arquivo ('Nome_do_Jogo-PPSA08329-US-PS5'),
Content ID, publisher, Publisher ID, regiao e URL.
Usa somente a biblioteca padrao do Python (sem pip install).
"""

import argparse
import csv
import html
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

SITES = {"PS5": "https://prosperopatches.com/", "PS4": "https://orbispatches.com/"}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
CAMPOS = ["title_id", "plataforma", "nome", "nome_arquivo", "content_id", "publisher", "publisher_id", "regiao", "url", "icone", "status"]
RE_CODIGO = re.compile(r"^[A-Z]{4}\d{5}$")


LETRAS_ESPECIAIS = str.maketrans({"ß": "ss", "æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O",
                                  "œ": "oe", "Œ": "OE", "ð": "d", "Ð": "D", "þ": "th", "Þ": "Th", "ł": "l", "Ł": "L"})


def nome_para_arquivo(nome: str, codigo: str, regiao: str = "", plataforma: str = "") -> str:
    """Monta 'Nome_do_Jogo-PPSA08329-US-PS5' so com letras sem acento, numeros, hifen e _ no lugar dos espacos.
    Codigo, regiao e plataforma vao separados por hifen (sem colchetes: o nome fica mais curto, o que
    importa para o limite do ShadowMountPlus). Sem regiao/plataforma informada, a parte (-US, -PS5...) e omitida.

    Ex.: "Assassin's Creed® Valhalla" -> "Assassins_Creed_Valhalla",
         "God of War Ragnarök" -> "God_of_War_Ragnarok", "Ratchet & Clank" -> "Ratchet_and_Clank".
    """
    nome = re.sub(r"[™®©℠]", "", nome)            # tira (TM) (R) (C) antes de normalizar
    nome = re.sub(r"[‐-―]", "-", nome)                      # travessoes viram hifen
    nome = unicodedata.normalize("NFKD", nome.translate(LETRAS_ESPECIAIS))
    nome = "".join(c for c in nome if not unicodedata.combining(c))   # tira acentos
    nome = nome.replace("&", " and ").replace(":", " - ")             # 'Jogo: Sub' -> 'Jogo - Sub'
    nome = re.sub(r"['’`´]", "", nome)                      # Assassin's -> Assassins
    nome = re.sub(r"[^A-Za-z0-9 \-]", " ", nome)                      # demais simbolos viram espaco
    nome = " ".join(nome.split())
    nome = re.sub(r"( -)+ ", " - ", nome).strip(" -")                 # ' - - ' -> ' - ' (Spider-Man fica)
    sufixo = ""
    for extra in (regiao, plataforma):
        extra = re.sub(r"[^A-Za-z0-9]", "", extra).upper()
        if extra:
            sufixo += f"-{extra}"
    return nome.replace(" ", "_") + f"-{codigo}{sufixo}"


def normalizar(codigo: str) -> str:
    """Aceita 'PPSA08329', 'ppsa-08329', 'PPSA 08329' e devolve 'PPSA08329'."""
    return re.sub(r"[^A-Za-z0-9]", "", codigo).upper()


def baixar(url: str, tentativas: int = 3) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as erro:
            # HTTPError (404, 500...) nao adianta repetir; falha de rede sim.
            if isinstance(erro, urllib.error.HTTPError) or tentativa == tentativas:
                raise
            time.sleep(3 * tentativa)


def campo_lateral(pagina: str, rotulo: str) -> str:
    """Le um item da barra lateral: <strong ...>Rotulo ...</strong> valor </li>."""
    padrao = rf"<strong[^>]*>\s*{re.escape(rotulo)}\b.*?</strong>(.*?)</li>"
    achado = re.search(padrao, pagina, re.S)
    if not achado:
        return ""
    texto = re.sub(r"<[^>]+>", " ", achado.group(1))
    return html.unescape(" ".join(texto.split()))


def consultar(codigo: str) -> dict:
    codigo = normalizar(codigo)
    resultado = dict.fromkeys(CAMPOS, "")
    resultado["title_id"] = codigo

    if not RE_CODIGO.match(codigo):
        resultado["status"] = "codigo invalido"
        return resultado

    # O orbispatches demora ~16s para responder codigo que nao conhece, entao so recebe CUSA;
    # demais prefixos (PPSA e codigos de disco) vao so ao prosperopatches, que responde rapido.
    plataformas = ["PS4"] if codigo.startswith("CUSA") else ["PS5"]
    pagina, titulo = "", None
    for plataforma in plataformas:
        url = SITES[plataforma] + codigo
        resultado.update(plataforma=plataforma, url=url)
        try:
            pagina = baixar(url)
        except urllib.error.HTTPError as erro:
            resultado["status"] = "nao encontrado" if erro.code == 404 else f"erro HTTP {erro.code}"
            continue
        except (urllib.error.URLError, TimeoutError) as erro:
            motivo = getattr(erro, "reason", erro)
            resultado["status"] = "erro de conexao: " + " ".join(str(motivo).split())[:120]
            continue
        titulo = re.search(r'<meta property="og:title" content="([^"]*)"', pagina)
        if titulo and ":" in titulo.group(1):
            break
        # Codigo inexistente: o site devolve a home/outra pagina, sem og:title "CODIGO: Nome".
        titulo = None
        resultado["status"] = "nao encontrado"

    if titulo is None:
        if resultado["status"] == "nao encontrado":
            resultado.update(plataforma="", url="")
        return resultado

    resultado["nome"] = html.unescape(titulo.group(1).split(":", 1)[1].strip())
    resultado["content_id"] = campo_lateral(pagina, "Content ID")
    resultado["publisher"] = campo_lateral(pagina, "Publisher").replace("View", "").strip()
    resultado["publisher_id"] = campo_lateral(pagina, "Publisher ID")
    resultado["regiao"] = campo_lateral(pagina, "Region").replace("Switch", "").strip()
    icone = re.search(r'class="game-icon[^"]*"[^>]*url\((https://[^)]+)\)', pagina)
    resultado["icone"] = icone.group(1) if icone else ""
    resultado["nome_arquivo"] = nome_para_arquivo(resultado["nome"], codigo, resultado["regiao"], resultado["plataforma"])
    resultado["status"] = "ok"
    return resultado


def ler_arquivo(caminho: str) -> list[str]:
    with open(caminho, encoding="utf-8-sig") as arq:
        return [linha.strip() for linha in arq if linha.strip() and not linha.startswith("#")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Consulta Title IDs de PS5 no prosperopatches.com")
    parser.add_argument("codigos", nargs="*", help="Title IDs, ex.: PPSA08329")
    parser.add_argument("-a", "--arquivo", help="arquivo texto com um codigo por linha")
    parser.add_argument("-o", "--saida", help="grava o resultado em CSV (separador ;)")
    parser.add_argument("-l", "--lista", help="grava um TXT so com as linhas 'Nome do Jogo [PPSAXXXXX]'")
    args = parser.parse_args()

    codigos = list(args.codigos)
    if args.arquivo:
        codigos += ler_arquivo(args.arquivo)
    if not codigos:
        codigo = input("Digite o Title ID (ex.: PPSA08329): ").strip()
        codigos = [codigo] if codigo else []
    if not codigos:
        parser.print_help()
        return 1

    resultados = []
    for indice, codigo in enumerate(codigos):
        if indice:
            time.sleep(1)  # pausa entre consultas para nao sobrecarregar o site
        r = consultar(codigo)
        resultados.append(r)
        if r["status"] == "ok":
            print(f"{r['title_id']}  [{r['plataforma']}]  {r['nome']}")
            print(f"    Arquivo    : {r['nome_arquivo']}")
            print(f"    Content ID : {r['content_id']}")
            print(f"    Publisher  : {r['publisher']} ({r['publisher_id']})")
            print(f"    Regiao     : {r['regiao']}")
            print(f"    URL        : {r['url']}")
        else:
            print(f"{r['title_id']}  -> {r['status']}")

    if args.saida:
        with open(args.saida, "w", newline="", encoding="utf-8-sig") as arq:
            escritor = csv.DictWriter(arq, fieldnames=CAMPOS, delimiter=";")
            escritor.writeheader()
            escritor.writerows(resultados)
        print(f"\nCSV gravado em: {args.saida}")

    if args.lista:
        with open(args.lista, "w", encoding="utf-8") as arq:
            arq.writelines(r["nome_arquivo"] + "\n" for r in resultados if r["status"] == "ok")
        print(f"Lista de nomes gravada em: {args.lista}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
