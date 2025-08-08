import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk


class RecordingIndicator(Toplevel):
    def __init__(self, parent, recording_module):
        super().__init__(parent)
        self.recording_module = recording_module
        self.animation_id = None
        self.logo_photo = None

        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.withdraw()

        # Container principal que será reconfigurado para cada modo
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_preparation_mode(self):
        self._clear_container()
        self.container.configure(bg='#2b2b2b', padx=10, pady=5)

        # Ícone e texto para o modo de preparação
        prep_label = tk.Label(self.container, text="● Preparando", font=("Segoe UI", 12, "bold"), fg="#ffcc00", bg=self.cget('bg'))
        prep_label.pack(side="left", padx=(0, 10))

        info_label = tk.Label(self.container, text="Pronto para gravar (Ctrl+F10)", font=("Segoe UI", 10), fg="white", bg=self.cget('bg'))
        info_label.pack(side="left", padx=(0, 15))

        start_button = tk.Button(self.container, text="INICIAR", font=("Segoe UI", 9, "bold"), fg="black", bg="#ffcc00", relief="flat",
                                 command=self.recording_module.start_recording_mode, bd=0, padx=10, pady=2)
        start_button.pack(side="left", padx=(0, 5))

        self._display_window()

    def show(self):
        """ Mostra o indicador no modo de gravação normal. """
        self._clear_container()
        self.container.configure(bg='#2b2b2b', padx=10, pady=5)

        self.rec_label = tk.Label(self.container, text="REC", font=("Segoe UI", 12, "bold"), fg="#ff0000", bg=self.cget('bg'))
        self.rec_label.pack(side="left", padx=(0, 10))

        self.time_label = tk.Label(self.container, text="00:00:00", font=("Segoe UI", 12, "bold"), fg="white", bg=self.cget('bg'))
        self.time_label.pack(side="left", padx=(0, 10))

        self.info_label = tk.Label(self.container, text="Ctrl+F10 para parar", font=("Segoe UI", 10), fg="white", bg=self.cget('bg'))
        self.info_label.pack(side="left", padx=(0, 15))

        stop_button = tk.Button(self.container, text="PARAR", font=("Segoe UI", 9, "bold"), fg="white", bg="#c70000", relief="flat",
                                command=self.recording_module.stop_recording, bd=0, padx=10, pady=2)
        stop_button.pack(side="left", padx=(0, 5))

        self.update_time(0)
        self._display_window()
        if self.animation_id is None:
            self._animate_rec()

    def _display_window(self):
        self.update_idletasks()
        x = self.master.winfo_screenwidth() - self.winfo_reqwidth() - 20
        y = 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def _animate_rec(self):
        if not self.winfo_exists() or not self.recording_module.is_recording:
            if self.animation_id:
                self.after_cancel(self.animation_id)
                self.animation_id = None
            return

        current_color = self.rec_label.cget("fg")
        new_color = self.cget('bg') if current_color == '#ff0000' else '#ff0000'
        self.rec_label.config(fg=new_color)
        self.animation_id = self.after(700, self._animate_rec)

    def hide(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.animation_id = None
        self.withdraw()

    def update_time(self, elapsed_seconds):
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            secs = int(elapsed_seconds)
            mins, secs = divmod(secs, 60)
            hrs, mins = divmod(mins, 60)
            self.time_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
