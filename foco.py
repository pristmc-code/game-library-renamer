"""Traz o navegador padrao para a frente depois de abrir um link (Loja/YouTube).

O Windows nao deixa um processo em segundo plano (o servidor do app) tirar o foco da janela
ativa: o navegador so pisca na barra de tarefas, e se estiver minimizado continua minimizado.
Aqui, logo depois de abrir o link, procuramos a janela do navegador padrao, restauramos se
estiver minimizada e a colocamos em primeiro plano "emprestando" a entrada da janela ativa
(a janela do app, onde o usuario acabou de clicar). Somente Windows; falhas sao ignoradas.
"""

import ctypes
import os
import re
import sys
import threading
import time
import winreg
from ctypes import wintypes

TITULO_APP = "Game Library Renamer"
ESPERA_INICIAL_S = 0.6
TENTATIVAS = 10
INTERVALO_S = 0.3


def _exe_navegador_padrao() -> str:
    """Nome do .exe do navegador padrao (ex.: chrome.exe), lido da associacao do https."""
    try:
        chave = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chave) as k:
            prog_id = winreg.QueryValueEx(k, "ProgId")[0]
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\shell\open\command") as k:
            comando = winreg.QueryValueEx(k, "")[0]
    except OSError:
        return ""
    achado = re.match(r'\s*"([^"]+)"|\s*(\S+)', comando)
    caminho = (achado.group(1) or achado.group(2)) if achado else ""
    return os.path.basename(caminho).lower()


def _exe_do_processo(pid: int) -> str:
    kernel32 = ctypes.windll.kernel32
    processo = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not processo:
        return ""
    try:
        buffer = ctypes.create_unicode_buffer(1024)
        tamanho = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(processo, 0, buffer, ctypes.byref(tamanho)):
            return os.path.basename(buffer.value).lower()
        return ""
    finally:
        kernel32.CloseHandle(processo)


def _janela_do_navegador(exe: str) -> int:
    """Janela principal mais ao topo (ordem Z) do navegador, ignorando a janela do proprio app."""
    user32 = ctypes.windll.user32
    achada = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visitar(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.GetWindow(hwnd, 4):  # 4 = GW_OWNER
            return True
        titulo = ctypes.create_unicode_buffer(300)
        user32.GetWindowTextW(hwnd, titulo, 300)
        if not titulo.value or titulo.value == TITULO_APP:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if _exe_do_processo(pid.value) == exe:
            achada.append(hwnd)
            return False  # EnumWindows percorre do topo para baixo: a primeira e a mais recente
        return True

    user32.EnumWindows(visitar, 0)
    return achada[0] if achada else 0


def _trazer(hwnd: int) -> None:
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    # Liga a entrada desta thread a da janela ativa (a do app): assim o Windows aceita a troca de foco.
    ativa = user32.GetForegroundWindow()
    thread_ativa = user32.GetWindowThreadProcessId(ativa, None)
    minha = kernel32.GetCurrentThreadId()
    ligado = bool(thread_ativa) and thread_ativa != minha and user32.AttachThreadInput(minha, thread_ativa, True)
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if ligado:
            user32.AttachThreadInput(minha, thread_ativa, False)
    if user32.GetForegroundWindow() != hwnd:
        # Ultimo recurso: um toque na tecla Alt libera a troca de foco para este processo.
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)  # KEYEVENTF_KEYUP
        user32.SetForegroundWindow(hwnd)


def _janela_por_titulo(trecho: str) -> int:
    """Primeira janela principal visivel (ordem Z) cujo titulo contem o trecho."""
    user32 = ctypes.windll.user32
    achada = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visitar(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.GetWindow(hwnd, 4):  # 4 = GW_OWNER
            return True
        titulo = ctypes.create_unicode_buffer(300)
        user32.GetWindowTextW(hwnd, titulo, 300)
        if trecho.lower() in titulo.value.lower():
            achada.append(hwnd)
            return False
        return True

    user32.EnumWindows(visitar, 0)
    return achada[0] if achada else 0


def trazer_janela_com_titulo(trecho: str) -> None:
    """Traz para a frente a janela cujo titulo contem o trecho (ex.: o Bloco de Notas com o INI)."""
    if sys.platform != "win32":
        return

    def tarefa():
        time.sleep(ESPERA_INICIAL_S)
        for _ in range(TENTATIVAS):
            hwnd = _janela_por_titulo(trecho)
            if hwnd:
                try:
                    _trazer(hwnd)
                except OSError:
                    pass
                return
            time.sleep(INTERVALO_S)

    threading.Thread(target=tarefa, daemon=True).start()


def trazer_navegador_para_frente() -> None:
    """Chamar logo depois de webbrowser.open(); roda em segundo plano."""
    if sys.platform != "win32":
        return

    def tarefa():
        exe = _exe_navegador_padrao()
        if not exe:
            return
        time.sleep(ESPERA_INICIAL_S)  # tempo para o navegador abrir a aba nova
        for _ in range(TENTATIVAS):
            hwnd = _janela_do_navegador(exe)
            if hwnd:
                try:
                    _trazer(hwnd)
                except OSError:
                    pass
                return
            time.sleep(INTERVALO_S)

    threading.Thread(target=tarefa, daemon=True).start()
