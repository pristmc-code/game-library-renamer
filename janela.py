"""Abre a tela do app numa janela propria (modo aplicativo do Edge/Chrome), sem barra de
endereco nem abas. Sem Edge/Chrome, cai no navegador padrao.

A janela usa um perfil proprio (pasta 'janela' ao lado do app), assim ela roda num processo
separado do navegador do usuario: fechar a janela encerra o app, e o app consegue fechar a janela.
"""

import os
import subprocess
import time
import webbrowser
from pathlib import Path

import ftp_ps5
import identidade_janela

PASTA_PERFIL = ftp_ps5.PASTA_APP / "janela"
TAMANHO = "1220,900"  # tamanho ao sair do modo maximizado (identidade_janela maximiza ao abrir)
SAIDA_RAPIDA_S = 5  # o processo saiu logo apos abrir: outra janela do mesmo perfil assumiu


def _navegador_app() -> Path | None:
    candidatos = []
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidatos += [Path(base) / "Microsoft/Edge/Application/msedge.exe",
                           Path(base) / "Google/Chrome/Application/chrome.exe"]
    return next((c for c in candidatos if c.exists()), None)


def abrir(endereco: str) -> subprocess.Popen | None:
    """Abre a janela do app. Devolve o processo da janela (ou None se abriu no navegador padrao)."""
    exe = _navegador_app()
    if not exe:
        webbrowser.open(endereco)
        return None
    # Sem a camada de compatibilidade (__COMPAT_LAYER, herdada do instalador): com ela o Edge se
    # relanca num processo novo e o original sai; o app perdia a janela (icone voltava a ser o do
    # Edge e fechar a janela nao encerrava o app).
    ambiente = {k: v for k, v in os.environ.items() if k.upper() != "__COMPAT_LAYER"}
    processo = subprocess.Popen([str(exe), f"--app={endereco}", f"--user-data-dir={PASTA_PERFIL}",
                                 f"--window-size={TAMANHO}", "--no-first-run", "--no-default-browser-check",
                                 "--edge-skip-compat-layer-relaunch"], env=ambiente)
    identidade_janela.acompanhar(processo)  # icone/atalho proprios na barra de tarefas (nao os do Edge)
    return processo


def ao_fechar(processo: subprocess.Popen, acao) -> None:
    """Executa acao() quando o usuario fechar a janela (chamar numa thread)."""
    inicio = time.time()
    processo.wait()
    if time.time() - inicio < SAIDA_RAPIDA_S:
        return  # nao era a janela de verdade (repassou para outra ja aberta): nao encerra o app
    acao()


def fechar(processo: subprocess.Popen | None) -> None:
    if processo and processo.poll() is None:
        processo.terminate()
