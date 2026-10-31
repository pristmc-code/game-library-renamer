"""Da ao processo do app a identidade do Game Library Renamer na barra de tarefas.

O AppUserModelID e o mesmo do atalho criado pelo instalador: a janela agrupa com ele e, ao
fixar, usa o icone e o atalho do app. Somente Windows; em qualquer falha nao faz nada.
"""

import ctypes
import sys

ID_APP = "PristMC.GameLibraryRenamer"


def definir_id_processo() -> None:
    """Chamar antes de criar a janela."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ID_APP)
    except (OSError, AttributeError):
        pass
