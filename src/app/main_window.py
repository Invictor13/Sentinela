import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
import random
import os
import subprocess
import sys

from src.utils import resource_path
from src.ui.settings_window import SettingsWindow

COR_FUNDO_JANELA = "#f0f5f0"
COR_CARD = "#ffffff"
COR_TEXTO_PRINCIPAL = "#005a36"
COR_TEXTO_SECUNDARIO = "#555555"
COR_BOTAO = "#00995D"
COR_BOTAO_HOVER = "#007a4a"
COR_BOTAO_SECUNDARIO = "#7f8c8d"
COR_BOTAO_SECUNDARIO_HOVER = "#6c7a7d"

class MainApplication(tk.Frame):
    def __init__(self, parent, capture_module, recording_module, app_config):
        super().__init__(parent, bg=COR_FUNDO_JANELA)
        self.parent = parent
        self.capture_module = capture_module
        self.recording_module = recording_module
        self.app_config = app_config
        self.record_all_screens_var = tk.BooleanVar(value=False)

        # 1. Configuração de Tela Cheia Absoluta
        self.parent.attributes('-fullscreen', True)
        self.parent.bind('<Escape>', self.exit_fullscreen)

        # 2. Configuração do Grid para Centralização
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()

    def exit_fullscreen(self, event=None):
        """Função para sair do modo de tela cheia."""
        self.parent.attributes('-fullscreen', False)

    def create_widgets(self):
        # 3. Cálculo de Dimensões Proporcionais
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        frame_width = int(screen_width * 0.5)
        frame_height = int(screen_height * 0.6)

        self.main_card_frame = tk.Frame(
            self,
            bg=COR_CARD,
            bd=1,
            relief="solid",
            width=frame_width,
            height=frame_height
        )
        # 4. Posicionamento do Frame no Grid Central
        self.main_card_frame.grid(row=0, column=0)
        # Impede que o frame se redimensione para caber os widgets internos
        self.main_card_frame.grid_propagate(False)

        # --- Widgets Internos (sem alteração na lógica, apenas no parent) ---
        header_container = tk.Frame(self.main_card_frame, bg=COR_CARD, padx=20, pady=15)
        header_container.pack(fill="x", expand=True, pady=(10,0))
        try:
            logo_image = Image.open(resource_path("logo.png"))
            logo_image.thumbnail((200, 60))
            self.logo_tk = ImageTk.PhotoImage(logo_image)
            tk.Label(header_container, image=self.logo_tk, bg=COR_CARD).pack(pady=(0,10))
        except FileNotFoundError:
            pass
        tk.Label(header_container, text="Sentinela Unimed", font=("Segoe UI", 26, "bold"), bg=COR_CARD, fg=COR_TEXTO_PRINCIPAL).pack()
        tk.Label(header_container, text="Gravador de evidências simples e seguro", font=("Segoe UI", 10), bg=COR_CARD, fg=COR_TEXTO_SECUNDARIO).pack(pady=(0,10))
        tk.Frame(self.main_card_frame, height=1, bg="#e0e0e0").pack(fill="x", padx=40, pady=(15,10))

        content_container = tk.Frame(self.main_card_frame, bg=COR_CARD, padx=40, pady=20)
        content_container.pack(expand=True, fill="both")

        btn1 = tk.Button(content_container, text="INICIAR CAPTURA (F9)", font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=20, pady=8, command=self.capture_module.start_capture_session)
        btn1.pack(pady=(5,10), fill='x')
        btn2 = tk.Button(content_container, text="INICIAR GRAVAÇÃO (F10)", font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=20, pady=8, command=lambda: self.recording_module.enter_preparation_mode(record_all_screens=self.record_all_screens_var.get()))
        btn2.pack(pady=(5,10), fill='x')

        record_all_checkbox = tk.Checkbutton(
            content_container,
            text="Gravar todas as telas simultaneamente (experimental)",
            variable=self.record_all_screens_var,
            bg=COR_CARD,
            fg=COR_TEXTO_SECUNDARIO,
            activebackground=COR_CARD,
            activeforeground=COR_TEXTO_PRINCIPAL,
            selectcolor=COR_FUNDO_JANELA,
            font=("Segoe UI", 9)
        )
        record_all_checkbox.pack(pady=(0, 10))

        for btn in [btn1, btn2]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_HOVER))
            btn.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO))

        footer_frame = tk.Frame(self.main_card_frame, bg="#f5f5f5", pady=5)
        footer_frame.pack(side="bottom", fill="x", pady=(10,0))

        btn_open_folder = tk.Button(footer_frame, text="Abrir Pasta de Evidências", font=("Segoe UI", 8, "bold"), command=self.open_evidence_folder, relief=tk.FLAT, bg=COR_BOTAO_SECUNDARIO, fg="white")
        btn_open_folder.pack(side=tk.LEFT, padx=10)
        btn_open_folder.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_SECUNDARIO_HOVER))
        btn_open_folder.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO_SECUNDARIO))

        tk.Label(footer_frame, text="Código by Victor Ladislau Viana", font=("Segoe UI", 8), bg=footer_frame.cget('bg'), fg=COR_TEXTO_SECUNDARIO).pack(side=tk.LEFT, padx=10)

        btn_settings = tk.Button(footer_frame, text="⚙", font=("Segoe UI", 12), command=self.open_settings, relief=tk.FLAT, bg=footer_frame.cget('bg'), fg=COR_TEXTO_SECUNDARIO)
        btn_settings.pack(side=tk.RIGHT, padx=10)

    def open_evidence_folder(self):
        folder_to_open = self.app_config["DefaultSaveLocation"]
        try:
            subprocess.Popen(f'explorer "{os.path.realpath(folder_to_open)}"')
        except Exception as e:
            print(f"Não foi possível abrir a pasta de evidências: {e}")

    def open_settings(self):
        SettingsWindow(self.parent, self.app_config, self.on_settings_closed)

    def on_settings_closed(self, new_save_path):
        self.app_config["DefaultSaveLocation"] = new_save_path
        self.capture_module.save_path = new_save_path
        self.recording_module.save_path = new_save_path
