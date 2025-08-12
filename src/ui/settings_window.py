import tkinter as tk
from tkinter import Toplevel, filedialog, messagebox, ttk
import os
from tkinter import font as tkfont

from src.config.settings import save_app_config

COR_FUNDO_JANELA = "#f0f5f0"
COR_TEXTO_PRINCIPAL = "#005a36"
COR_TEXTO_SECUNDARIO = "#555555"

class SettingsWindow(Toplevel):
    def __init__(self, parent, app_config, on_close_callback=None, is_first_run=False):
        super().__init__(parent)
        self.app_config = app_config
        self.on_close_callback = on_close_callback
        self.is_first_run = is_first_run

        # --- Window Setup ---
        if self.is_first_run:
            self.title("Bem-vindo ao Sentinela!")
            # Maximized state for the welcome screen
            self.state('zoomed')
        else:
            self.title("Configurações")
            self.geometry("500x500") # Normal size for subsequent runs
            self.resizable(False, False)

        self.configure(bg=COR_FUNDO_JANELA)
        self.transient(parent)
        self.grab_set()
        self.wm_attributes("-topmost", True)

        # --- Layout Refactoring ---
        if self.is_first_run:
            self.create_welcome_layout()
        else:
            self.create_standard_layout()

    def create_welcome_layout(self):
        """Creates a more elegant, spacious layout for the first run."""
        # Main container with padding
        container = tk.Frame(self, bg=COR_FUNDO_JANELA, padx=40, pady=30)
        container.pack(expand=True, fill="both")

        # --- Header ---
        tk.Label(container, text="Bem-vindo ao Sentinela!", font=("Segoe UI", 24, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(pady=(10, 5))
        tk.Label(container, text="Vamos configurar rapidamente suas preferências. Você pode alterá-las a qualquer momento no menu principal.",
                 font=("Segoe UI", 12), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).pack(pady=(0, 20))

        # --- Content Frame ---
        content_frame = tk.Frame(container, bg=COR_FUNDO_JANELA)
        content_frame.pack(expand=True, fill="x")

        # Center the settings in the middle of the screen
        settings_container = tk.Frame(content_frame, bg=COR_FUNDO_JANELA)
        settings_container.pack(expand=True)

        # Re-usable font
        title_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        label_font = ("Segoe UI", 11)

        # --- Section: Save Path ---
        path_frame = tk.Frame(settings_container, bg=COR_FUNDO_JANELA)
        path_frame.pack(fill='x', pady=10)
        tk.Label(path_frame, text="Pasta de Destino", font=title_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 5))

        self.save_path_var = tk.StringVar(value=self.app_config["DefaultSaveLocation"])
        path_entry_frame = tk.Frame(path_frame, bg=COR_FUNDO_JANELA)
        path_entry_frame.pack(fill='x')
        tk.Entry(path_entry_frame, textvariable=self.save_path_var, state="readonly", font=label_font).pack(side="left", expand=True, fill="x", ipady=4)
        tk.Button(path_entry_frame, text="Procurar...", command=self.browse_save_path, font=label_font).pack(side="left", padx=(10, 0))

        ttk.Separator(settings_container, orient='horizontal').pack(fill='x', pady=15)

        # --- Section: Recording Quality ---
        quality_frame = tk.Frame(settings_container, bg=COR_FUNDO_JANELA)
        quality_frame.pack(fill='x', pady=10)
        tk.Label(quality_frame, text="Qualidade de Vídeo", font=title_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 5))

        self.quality_var = tk.StringVar(value=self.app_config.get("RecordingQuality", "high"))
        style = ttk.Style()
        style.configure("TRadiobutton", background=COR_FUNDO_JANELA, foreground=COR_TEXTO_SECUNDARIO, font=label_font)
        ttk.Radiobutton(quality_frame, text="Full HD (MP4) - Alta Qualidade, Ideal para Edição e Visualização Local", variable=self.quality_var, value="high", style="TRadiobutton").pack(anchor="w")
        ttk.Radiobutton(quality_frame, text="HD (WEB) - Otimizado para o compartilhamento rápido.", variable=self.quality_var, value="compact", style="TRadiobutton").pack(anchor="w")

        ttk.Separator(settings_container, orient='horizontal').pack(fill='x', pady=15)

        # --- Section: Hotkeys ---
        hotkey_frame = tk.Frame(settings_container, bg=COR_FUNDO_JANELA)
        hotkey_frame.pack(fill='x', pady=10)
        tk.Label(hotkey_frame, text="Atalhos", font=title_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 10))

        hotkey_grid = tk.Frame(hotkey_frame, bg=COR_FUNDO_JANELA)
        hotkey_grid.pack(fill='x')
        hotkey_grid.columnconfigure(1, weight=1)

        # Capture Hotkey
        tk.Label(hotkey_grid, text="Captura de Tela:", font=label_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.capture_hotkey_var = tk.StringVar(value=self.app_config.get("CaptureHotkey", "F9"))
        tk.Entry(hotkey_grid, textvariable=self.capture_hotkey_var, state="readonly", font=label_font).grid(row=0, column=1, sticky="ew")
        tk.Button(hotkey_grid, text="Alterar...", command=lambda: self.change_hotkey_dialog('capture'), font=label_font).grid(row=0, column=2, padx=(10, 0))

        # Record Hotkey
        tk.Label(hotkey_grid, text="Gravação de Vídeo:", font=label_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10,0))
        self.record_hotkey_var = tk.StringVar(value=self.app_config.get("RecordHotkey", "F10"))
        tk.Entry(hotkey_grid, textvariable=self.record_hotkey_var, state="readonly", font=label_font).grid(row=1, column=1, sticky="ew", pady=(10,0))
        tk.Button(hotkey_grid, text="Alterar...", command=lambda: self.change_hotkey_dialog('record'), font=label_font).grid(row=1, column=2, padx=(10, 0), pady=(10,0))


        # --- Footer ---
        footer_frame = tk.Frame(container, bg=COR_FUNDO_JANELA)
        footer_frame.pack(side="bottom", fill="x", pady=(20, 0))

        save_button = tk.Button(footer_frame, text="Salvar e Continuar", command=self.save_settings, font=("Segoe UI", 12, "bold"), bg="#007a4a", fg="white", relief="flat", padx=20, pady=10)
        save_button.pack()

    def create_standard_layout(self):
        """Creates the original, compact layout for subsequent runs."""
        main_frame = tk.Frame(self, bg=COR_FUNDO_JANELA, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        current_row = 0
        title_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        # --- Editable Hotkeys ---
        tk.Label(main_frame, text="Atalhos", font=title_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=current_row, column=0, columnspan=3, sticky="w", pady=(0, 10))
        current_row += 1

        # Capture Hotkey
        tk.Label(main_frame, text="Captura de Tela:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=current_row, column=0, sticky="w", pady=(0, 5))
        self.capture_hotkey_var = tk.StringVar(value=self.app_config.get("CaptureHotkey", "F9"))
        tk.Entry(main_frame, textvariable=self.capture_hotkey_var, state="readonly", width=20).grid(row=current_row, column=1, sticky="ew", padx=5)
        tk.Button(main_frame, text="Alterar...", command=lambda: self.change_hotkey_dialog('capture'), font=("Segoe UI", 9)).grid(row=current_row, column=2, padx=(5, 0))
        current_row += 1

        # Record Hotkey
        tk.Label(main_frame, text="Gravação de Vídeo:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=current_row, column=0, sticky="w", pady=(0, 5))
        self.record_hotkey_var = tk.StringVar(value=self.app_config.get("RecordHotkey", "F10"))
        tk.Entry(main_frame, textvariable=self.record_hotkey_var, state="readonly", width=20).grid(row=current_row, column=1, sticky="ew", padx=5)
        tk.Button(main_frame, text="Alterar...", command=lambda: self.change_hotkey_dialog('record'), font=("Segoe UI", 9)).grid(row=current_row, column=2, padx=(5, 0))
        current_row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=15)
        current_row += 1

        # --- Save Path ---
        tk.Label(main_frame, text="Pasta Padrão", font=title_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=current_row, column=0, sticky="w", pady=(0, 5))
        current_row += 1

        self.save_path_var = tk.StringVar(value=self.app_config["DefaultSaveLocation"])
        tk.Entry(main_frame, textvariable=self.save_path_var, state="readonly").grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        browse_button = tk.Button(main_frame, text="Procurar...", command=self.browse_save_path, font=("Segoe UI", 9))
        browse_button.grid(row=current_row, column=2, padx=(5, 0))
        current_row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=15)
        current_row += 1

        # Quality Settings
        tk.Label(main_frame, text="Qualidade de Gravação", font=title_font, bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=current_row, column=0, sticky="w", pady=(0, 5))
        current_row += 1

        self.quality_var = tk.StringVar(value=self.app_config.get("RecordingQuality", "high"))

        quality_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        quality_frame.grid(row=current_row, column=0, columnspan=3, sticky="w", padx=20)
        current_row += 1

        style = ttk.Style()
        style.configure("TRadiobutton", background=COR_FUNDO_JANELA, foreground=COR_TEXTO_SECUNDARIO)

        ttk.Radiobutton(quality_frame, text="Full HD (MP4) - Alta Qualidade, Ideal para Edição e Visualização Local", variable=self.quality_var, value="high", style="TRadiobutton").pack(anchor="w")
        ttk.Radiobutton(quality_frame, text="HD (WEB) - Otimizado para o compartilhamento rápido.", variable=self.quality_var, value="compact", style="TRadiobutton").pack(anchor="w")

        buttons_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        buttons_frame.grid(row=current_row, column=0, columnspan=3, pady=(20,0))

        # --- Button Text Change for First Run ---
        save_button_text = "Salvar e Continuar" if self.is_first_run else "Salvar Configurações"
        tk.Button(buttons_frame, text=save_button_text, command=self.save_settings, font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        tk.Button(buttons_frame, text="Fechar", command=self.destroy, font=("Segoe UI", 10)).pack(side="left", padx=10)

        main_frame.columnconfigure(1, weight=1)

    def change_hotkey_dialog(self, hotkey_type):
        dialog = Toplevel(self)
        dialog.title("Alterar Atalho")
        dialog.geometry("300x100")
        dialog.configure(bg=COR_FUNDO_JANELA)
        dialog.transient(self)
        dialog.grab_set()
        dialog.wm_attributes("-topmost", True)

        label = tk.Label(dialog, text="Pressione a nova tecla de atalho...", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO)
        label.pack(pady=20, expand=True)

        def on_key_press(event):
            key_name = event.keysym
            if event.state & 4:  # Control
                key_name = f"Ctrl + {key_name}"
            if event.state & 1:  # Shift
                key_name = f"Shift + {key_name}"
            if event.state & 8:  # Alt
                key_name = f"Alt + {key_name}"

            if hotkey_type == 'capture':
                self.capture_hotkey_var.set(key_name)
            else:
                self.record_hotkey_var.set(key_name)

            dialog.destroy()

        dialog.bind("<KeyPress>", on_key_press)

    def browse_save_path(self):
        new_path = filedialog.askdirectory(initialdir=self.save_path_var.get(), parent=self)
        if new_path:
            self.save_path_var.set(new_path)

    def save_settings(self):
        new_save_path = self.save_path_var.get()
        new_quality = self.quality_var.get()
        new_capture_hotkey = self.capture_hotkey_var.get()
        new_record_hotkey = self.record_hotkey_var.get()

        try:
            os.makedirs(new_save_path, exist_ok=True)
            with open(os.path.join(new_save_path, ".test"), "w") as f:
                f.write("test")
            os.remove(os.path.join(new_save_path, ".test"))
        except:
            messagebox.showerror("Erro de Caminho", "Não é possível escrever no caminho.", parent=self)
            return

        config_parser_obj = self.app_config["config_parser_obj"]

        if self.is_first_run:
            if not config_parser_obj.has_section('User'):
                config_parser_obj.add_section('User')
            config_parser_obj.set('User', 'has_run_before', 'true')

        save_app_config(
            config_parser_obj,
            new_save_path,
            new_quality,
            new_capture_hotkey,
            new_record_hotkey
        )
        self.app_config["DefaultSaveLocation"] = new_save_path
        self.app_config["RecordingQuality"] = new_quality
        self.app_config["CaptureHotkey"] = new_capture_hotkey
        self.app_config["RecordHotkey"] = new_record_hotkey
        self.app_config["HasRunBefore"] = True


        if self.on_close_callback:
            self.on_close_callback(new_save_path)

        messagebox.showinfo("Sucesso", "Configurações salvas. Reinicie o aplicativo para que os novos atalhos entrem em vigor.", parent=self)
        self.destroy()
