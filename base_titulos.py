"""Base local de Title IDs PS4/PS5 (andshrew/PlayStation-Titles, licenca MIT).

- Baixa o All_Titles.tsv (~6 MB, ~71 mil titulos, atualizado diariamente pelo autor) ao iniciar o app,
  so quando o arquivo mudou (download condicional por ETag).
- Consulta e instantanea e offline; o que nao estiver na base cai na consulta ao site (consulta_ps5).
- A base nao tem icone nem o nome por extenso do publisher: esses continuam vindo do site.
"""

import csv
import json
import threading
import time
import urllib.error
import urllib.request

import ftp_ps5
from consulta_ps5 import CAMPOS, SITES, USER_AGENT, nome_para_arquivo, normalizar

URL_BASE = "https://raw.githubusercontent.com/andshrew/PlayStation-Titles/main/All_Titles.tsv"
ARQUIVO_BASE = ftp_ps5.PASTA_APP / "base_titulos.tsv"
ARQUIVO_META = ftp_ps5.PASTA_APP / "base_titulos.json"

# Primeira letra do codigo de regiao da base -> sigla usada pelos sites (e no nome do arquivo).
REGIOES = {"U": "US", "E": "EU", "J": "JP", "H": "AS", "K": "KR", "I": "Internal"}
PLATAFORMAS = {"PPSA": "PS5", "CUSA": "PS4"}

_titulos: dict[str, dict] = {}
_trava = threading.Lock()
_estado = {"situacao": "carregando", "qtd": 0, "atualizada_em": "", "erro": ""}


def _carregar_arquivo() -> None:
    titulos: dict[str, dict] = {}
    with open(ARQUIVO_BASE, encoding="utf-8", newline="") as arq:
        for linha in csv.DictReader(arq, delimiter="\t"):
            title_id = (linha.get("titleId") or "").strip()
            codigo = normalizar(title_id[:9])
            # Mantem a entrada _00 quando o mesmo codigo aparece com _01 etc.
            if len(codigo) == 9 and (codigo not in titulos or title_id.endswith("_00")):
                titulos[codigo] = linha
    with _trava:
        _titulos.clear()
        _titulos.update(titulos)
        _estado["qtd"] = len(titulos)


def _baixar() -> bool:
    """Baixa a base se mudou. Devolve True se baixou um arquivo novo."""
    meta = {}
    try:
        meta = json.loads(ARQUIVO_META.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    cabecalhos = {"User-Agent": USER_AGENT}
    if meta.get("etag") and ARQUIVO_BASE.exists():
        cabecalhos["If-None-Match"] = meta["etag"]
    try:
        with urllib.request.urlopen(urllib.request.Request(URL_BASE, headers=cabecalhos), timeout=60) as resp:
            conteudo = resp.read()
            etag = resp.headers.get("ETag", "")
    except urllib.error.HTTPError as erro:
        if erro.code == 304:  # nao mudou desde o ultimo download
            return False
        raise
    if not conteudo.startswith(b"titleId\t"):
        raise ValueError("arquivo baixado nao tem o formato esperado")
    temporario = ARQUIVO_BASE.with_suffix(".tmp")
    temporario.write_bytes(conteudo)
    temporario.replace(ARQUIVO_BASE)
    meta = {"etag": etag, "baixado_em": time.strftime("%d/%m/%Y %H:%M")}
    ARQUIVO_META.write_text(json.dumps(meta), encoding="utf-8")
    return True


def atualizar() -> None:
    """Carrega a base do disco e, em seguida, baixa a versao nova se houver."""
    if ARQUIVO_BASE.exists():
        try:
            _carregar_arquivo()
            _estado["situacao"] = "ok"
        except (OSError, ValueError) as erro:
            _estado["erro"] = str(erro)
    try:
        if _baixar() or not _titulos:
            _carregar_arquivo()
        _estado.update(situacao="ok", erro="")
    except Exception as erro:  # sem internet: segue com a base do disco (se houver)
        _estado["erro"] = f"nao foi possivel atualizar a base: {erro}"
        if not _titulos:
            _estado["situacao"] = "indisponivel"
    try:
        _estado["atualizada_em"] = json.loads(ARQUIVO_META.read_text(encoding="utf-8")).get("baixado_em", "")
    except (OSError, ValueError):
        pass


def atualizar_em_segundo_plano() -> None:
    threading.Thread(target=atualizar, daemon=True).start()


def estado() -> dict:
    return dict(_estado)


def consultar_base(codigo: str) -> dict | None:
    """Monta o mesmo resultado de consulta_ps5.consultar a partir da base local (sem icone)."""
    codigo = normalizar(codigo)
    with _trava:
        linha = _titulos.get(codigo)
    if not linha or not (linha.get("name") or "").strip():
        return None
    plataforma = PLATAFORMAS.get(codigo[:4], "")
    regiao = REGIOES.get((linha.get("region") or " ")[0], "")
    nome = linha["name"].strip()
    resultado = dict.fromkeys(CAMPOS, "")
    resultado.update(
        title_id=codigo, plataforma=plataforma, nome=nome,
        nome_arquivo=nome_para_arquivo(nome, codigo, regiao, plataforma),
        content_id=(linha.get("contentId") or "").strip(),
        concept_id=(linha.get("conceptId") or "").strip(),
        publisher_id=(linha.get("publisherId") or "").strip(),
        regiao=regiao, url=SITES.get(plataforma, "") + codigo if plataforma else "",
        status="ok",
    )
    return resultado
