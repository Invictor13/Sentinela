import sys
import os

# Este é o Feitiço de Autoconhecimento.
# Ele adiciona a pasta raiz do projeto ao caminho do Python,
# permitindo que o executável encontre seus próprios módulos.
if getattr(sys, 'frozen', False):
    # Se estiver rodando como um executável compilado pelo PyInstaller
    project_root = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como um script normal
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Adiciona a raiz ao início do caminho de busca de módulos
sys.path.insert(0, project_root)

# --- O RESTANTE DOS IMPORTS VEM DEPOIS DESTE BLOCO ---
# Exemplo: from src.app.main_window import MainApplication
import tkinter as tk
import threading
import ctypes
from src.app.main_window import MainApplication
from src.core.capture import ScreenCaptureModule
from src.core.recording import ScreenRecordingModule
from src.core.hotkeys import key_listener_thread_proc
from src.app.tray_icon import setup_tray_icon
from src.config.settings import load_app_config
from src.ui.settings_window import SettingsWindow
from src.utils import resource_path

def main():
    # --- RITUAL DE INICIALIZAÇÃO ---

    # 1. Forja-se a janela principal, mas nas SOMBRAS.
    root = tk.Tk()
    root.withdraw() # ESTE É O FEITIÇO MAIS IMPORTANTE! Ele torna a janela principal invisível.

    # 2. Carrega-se a sabedoria (configurações).
    app_config = load_app_config()
    config_parser = app_config["config_parser_obj"]

    # 3. Verifica-se se é o Rito de Passagem (primeira execução).
    if not config_parser.has_option('User', 'has_run_before'):
        # É a primeira vez! Invoca-se a janela de configuração inicial.
        from src.ui.settings_window import SettingsWindow # Importação tardia

        settings_window = SettingsWindow(root, app_config, is_first_run=True)

        # O feitiço de maximização é aplicado APENAS à janela de boas-vindas.
        settings_window.state('zoomed')

        # Feitiço de centralização (garantia extra).
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f'{width}x{height}+{x}+{y}')

        # Torna a janela de boas-vindas o foco absoluto.
        settings_window.grab_set()
        root.wait_window(settings_window)

    root.mainloop()

if __name__ == "__main__":
    main()
