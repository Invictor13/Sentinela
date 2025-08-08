import tkinter as tk
from tkinter import Toplevel, filedialog, messagebox, ttk
import os

from ..config.settings import save_app_config

COR_FUNDO_JANELA = "#f0f5f0"
COR_TEXTO_PRINCIPAL = "#005a36"
COR_TEXTO_SECUNDARIO = "#555555"

class SettingsWindow(Toplevel):
    def __init__(self, parent, app_config, on_close_callback):
        super().__init__(parent)
        self.app_config = app_config
        self.on_close_callback = on_close_callback

        self.title("Configurações")
        self.geometry("500x280")
        self.configure(bg=COR_FUNDO_JANELA)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.wm_attributes("-topmost", True)

        main_frame = tk.Frame(self, bg=COR_FUNDO_JANELA, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="Atalhos (fixos para estabilidade):", font=("Segoe UI", 10, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))
        tk.Label(main_frame, text="Captura de Tela:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=1, column=0, sticky="w", pady=(0,5))
        tk.Label(main_frame, text="Shift + F9", font=("Segoe UI", 10, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=1, column=1, sticky="w", padx=5)
        tk.Label(main_frame, text="Gravação de Vídeo:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=2, column=0, sticky="w", pady=(0,5))
        tk.Label(main_frame, text="Shift + F10", font=("Segoe UI", 10, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=2, column=1, sticky="w", padx=5)

        tk.Label(main_frame, text="Pasta Padrão:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=3, column=0, sticky="w", pady=(10,0))

        self.save_path_var = tk.StringVar(value=self.app_config["DefaultSaveLocation"])
        tk.Entry(main_frame, textvariable=self.save_path_var, state="readonly").grid(row=3, column=1, sticky="ew", padx=5)

        browse_button = tk.Button(main_frame, text="Procurar...", command=self.browse_save_path, font=("Segoe UI", 9))
        browse_button.grid(row=3, column=2, padx=(5,0))

        # Quality Settings
        tk.Label(main_frame, text="Qualidade de Gravação:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=4, column=0, sticky="w", pady=(10, 0))

        self.quality_var = tk.StringVar(value=self.app_config.get("RecordingQuality", "high"))

        quality_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        quality_frame.grid(row=5, column=0, columnspan=3, sticky="w", padx=20)

        style = ttk.Style()
        style.configure("TRadiobutton", background=COR_FUNDO_JANELA, foreground=COR_TEXTO_SECUNDARIO)

        ttk.Radiobutton(quality_frame, text="Full HD (MP4) - Ideal para edição e visualização local.", variable=self.quality_var, value="high", style="TRadiobutton").pack(anchor="w")
        ttk.Radiobutton(quality_frame, text="Web (720p) - Otimizado para compartilhamento rápido.", variable=self.quality_var, value="compact", style="TRadiobutton").pack(anchor="w")

        buttons_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=(20,0))

        tk.Button(buttons_frame, text="Salvar Configurações", command=self.save_settings, font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        tk.Button(buttons_frame, text="Fechar", command=self.destroy, font=("Segoe UI", 10)).pack(side="left", padx=10)

        main_frame.columnconfigure(1, weight=1)

    def browse_save_path(self):
        new_path = filedialog.askdirectory(initialdir=self.save_path_var.get(), parent=self)
        if new_path:
            self.save_path_var.set(new_path)

    def save_settings(self):
        new_save_path = self.save_path_var.get()
        new_quality = self.quality_var.get()
        try:
            os.makedirs(new_save_path, exist_ok=True)
            with open(os.path.join(new_save_path, ".test"), "w") as f:
                f.write("test")
            os.remove(os.path.join(new_save_path, ".test"))
        except:
            messagebox.showerror("Erro de Caminho", "Não é possível escrever no caminho.", parent=self)
            return

        save_app_config(self.app_config["config_parser_obj"], new_save_path, new_quality)
        self.app_config["DefaultSaveLocation"] = new_save_path
        self.app_config["RecordingQuality"] = new_quality

        if self.on_close_callback:
            self.on_close_callback(new_save_path)

        messagebox.showinfo("Sucesso", "Configurações salvas.", parent=self)
        self.destroy()
