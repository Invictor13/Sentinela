import tkinter as tk
import threading
import ctypes
import os
import sys
from .app.main_window import MainApplication
from .core.capture import ScreenCaptureModule
from .core.recording import ScreenRecordingModule
from .core.hotkeys import key_listener_thread_proc
from .app.tray_icon import setup_tray_icon
from .config.settings import load_app_config
from .ui.settings_window import SettingsWindow

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, "assets", relative_path)

def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e:
            print(f"Alerta de DPI: Não foi possível configurar a sensibilidade de DPI. Erro: {e}")

    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal inicialmente
    root.state('zoomed') # Inicia a janela maximizada

    # Função para sair do modo maximizado/tela cheia
    def exit_zoom(event=None):
        root.state('normal')

    # Vinculando a tecla Escape a esta função
    root.bind('<Escape>', exit_zoom)

    root.title("Sentinela Unimed")
    root.protocol("WM_DELETE_WINDOW", root.withdraw)
    root.geometry("1280x720")

    try:
        icon_path_ico = resource_path('logo.ico')
        root.iconbitmap(icon_path_ico)
    except (tk.TclError, FileNotFoundError):
        icon_path_ico = None

    app_config = load_app_config()
    save_path = app_config["DefaultSaveLocation"]

    # --- First Run Check ---
    if not app_config.get("HasRunBefore", False):
        # This blocks until the window is closed
        settings_window = SettingsWindow(root, app_config, is_first_run=True)
        root.wait_window(settings_window)
        # The config object in memory might have been updated, so we get the latest save_path
        save_path = app_config["DefaultSaveLocation"]


    capture_module = ScreenCaptureModule(root, save_path)
    recording_module = ScreenRecordingModule(root, save_path)
    main_app = MainApplication(root, capture_module, recording_module, app_config)
    main_app.pack(side="top", fill="both", expand=True)

    listener_thread = threading.Thread(
        target=key_listener_thread_proc,
        args=(capture_module, recording_module, root, main_app),
        daemon=True
    )
    listener_thread.start()

    tray_thread = threading.Thread(
        target=setup_tray_icon,
        args=(root, capture_module, recording_module, app_config),
        daemon=True
    )
    tray_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()
