"""Da a janela do app (que e do Edge/Chrome) a identidade do Game Library Renamer na barra de tarefas.

Sem isto o Windows trata a janela como "Microsoft Edge": agrupa com o Edge e, ao fixar, usa o
icone e o atalho do Edge. Aqui gravamos nas propriedades da janela (IPropertyStore):
  - AppUserModelID: o mesmo do atalho criado pelo instalador (agrupa com ele);
  - RelaunchCommand / RelaunchIconResource / RelaunchDisplayNameResource: o que o Windows usa
    ao fixar a janela (abre o GameLibraryRenamer.exe, com o nosso icone e nome).
Somente Windows; em qualquer falha apenas deixa a janela como esta.
"""

import ctypes
import sys
import threading
import uuid
from ctypes import wintypes

ID_APP = "PristMC.GameLibraryRenamer"
NOME_APP = "Game Library Renamer"
INTERVALO_S = 1.5

_FMTID_APPUSERMODEL = uuid.UUID("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3")
_IID_IPROPERTYSTORE = uuid.UUID("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")
_PID_ID, _PID_COMANDO, _PID_ICONE, _PID_NOME = 5, 2, 3, 4
_VT_LPWSTR = 31


class _GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8)]

    @classmethod
    def de(cls, valor: uuid.UUID) -> "_GUID":
        return cls.from_buffer_copy(valor.bytes_le)


class _PROPERTYKEY(ctypes.Structure):
    _fields_ = [("fmtid", _GUID), ("pid", wintypes.DWORD)]


class _PROPVARIANT(ctypes.Structure):
    # vt + 3 reservados (8 bytes) + uniao de 16 bytes; so usamos o ponteiro de texto (VT_LPWSTR).
    _fields_ = [("vt", wintypes.USHORT), ("r1", wintypes.USHORT), ("r2", wintypes.USHORT), ("r3", wintypes.USHORT),
                ("texto", ctypes.c_wchar_p), ("_resto", ctypes.c_void_p)]


def _comando_relancar() -> tuple[str, str]:
    """(linha de comando, icone) usados quando a janela e fixada na barra de tarefas."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"', f"{sys.executable},0"
    script = sys.argv[0]
    return f'"{sys.executable}" "{script}"', f"{sys.executable},0"


def _gravar(hwnd: int) -> bool:
    shell32 = ctypes.windll.shell32
    loja = ctypes.c_void_p()
    iid = _GUID.de(_IID_IPROPERTYSTORE)
    if shell32.SHGetPropertyStoreForWindow(wintypes.HWND(hwnd), ctypes.byref(iid), ctypes.byref(loja)) != 0 or not loja:
        return False
    vtbl = ctypes.cast(ctypes.cast(loja, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
    set_value = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(_PROPERTYKEY),
                                   ctypes.POINTER(_PROPVARIANT))(vtbl[6])
    commit = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p)(vtbl[7])
    release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])
    comando, icone = _comando_relancar()
    try:
        # Os dados de "relancar" vem antes do ID, como pede a documentacao do Windows.
        for pid, valor in ((_PID_COMANDO, comando), (_PID_ICONE, icone), (_PID_NOME, NOME_APP), (_PID_ID, ID_APP)):
            chave = _PROPERTYKEY(_GUID.de(_FMTID_APPUSERMODEL), pid)
            var = _PROPVARIANT(vt=_VT_LPWSTR, texto=valor)
            set_value(loja, ctypes.byref(chave), ctypes.byref(var))
        commit(loja)
        return True
    except OSError:
        return False
    finally:
        release(loja)


def _janelas_do_processo(pid: int) -> list[int]:
    user32 = ctypes.windll.user32
    achadas = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visitar(hwnd, _):
        dono = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(dono))
        # So janelas principais visiveis (sem janela "dona") do processo da janela do app.
        if dono.value == pid and user32.IsWindowVisible(hwnd) and not user32.GetWindow(hwnd, 4):  # 4 = GW_OWNER
            achadas.append(hwnd)
        return True

    user32.EnumWindows(visitar, 0)
    return achadas


def acompanhar(processo) -> None:
    """Enquanto o processo da janela existir, aplica a identidade nas janelas novas dele e as maximiza."""
    if sys.platform != "win32":
        return

    def laco():
        feitas: set[int] = set()
        while processo.poll() is None:
            for hwnd in _janelas_do_processo(processo.pid):
                if hwnd not in feitas and _gravar(hwnd):
                    feitas.add(hwnd)
                    # Abre maximizada (o Edge em modo --app ignora --start-maximized).
                    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            threading.Event().wait(INTERVALO_S)

    threading.Thread(target=laco, daemon=True).start()
