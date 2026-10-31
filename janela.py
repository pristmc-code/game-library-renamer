"""Mostra a tela do app numa janela propria do Game Library Renamer (pywebview + WebView2),
sem abrir o Edge/Chrome. Sem WebView2/pywebview, cai no navegador padrao.

A janela pertence ao proprio processo do app: icone e nome na barra de tarefas sao os do app,
fechar a janela encerra o app e o botao Sair fecha a janela.
"""

import webbrowser

import foco
import ftp_ps5
import identidade_janela

TITULO = "Game Library Renamer"
PASTA_PERFIL = ftp_ps5.PASTA_APP / "janela"  # dados da janela (WebView2), ao lado do app
ICONES = (ftp_ps5.PASTA_RECURSOS / "icone.ico", ftp_ps5.PASTA_APP / "instalador" / "icone.ico")

_janela = None


def disponivel() -> bool:
    try:
        import webview  # noqa: F401
        return True
    except Exception:
        return False


def abrir_navegador(endereco: str) -> None:
    """Reserva: sem a janela propria, abre a tela no navegador padrao."""
    webbrowser.open(endereco)


def mostrar(endereco: str) -> bool:
    """Abre a janela e so volta quando ela for fechada (precisa rodar na thread principal).
    Devolve False se a janela propria nao pode ser aberta (ai o chamador usa o navegador)."""
    global _janela
    try:
        import webview
        identidade_janela.definir_id_processo()  # agrupa com o atalho do instalador na barra de tarefas
        webview.settings["ALLOW_DOWNLOADS"] = True  # exportar TXT/CSV abre o "Salvar como"
        _janela = webview.create_window(TITULO, endereco, width=1220, height=900, min_size=(800, 600),
                                        maximized=True, text_select=True)
        icone = next((str(p) for p in ICONES if p.exists()), None)
        PASTA_PERFIL.mkdir(parents=True, exist_ok=True)
        webview.start(gui="edgechromium", private_mode=False, storage_path=str(PASTA_PERFIL), icon=icone)
        return True
    except Exception as erro:
        print(f"Aviso: janela propria indisponivel ({erro}) - abrindo no navegador padrao.")
        _janela = None
        return False


def trazer_para_frente() -> None:
    """Outra copia do app foi aberta: mostra a janela que ja existe."""
    if _janela:
        try:
            _janela.restore()
            _janela.show()
            foco.trazer_janela_com_titulo(TITULO)
        except Exception:
            pass


def fechar() -> None:
    if _janela:
        try:
            _janela.destroy()
        except Exception:
            pass
