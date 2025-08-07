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
        self.configure(bg='#2b2b2b')
        container = tk.Frame(self, bg=self.cget('bg'))
        container.pack(padx=10, pady=5)

        try:
            logo_image = Image.open("assets/logo.png").resize((20, 20), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(container, image=self.logo_photo, bg=self.cget('bg'))
            logo_label.pack(side="left", padx=(0, 5))
        except Exception as e:
            print(f"Alerta: Não foi possível carregar o ícone para o indicador de gravação. {e}")

        self.rec_label = tk.Label(container, text="REC", font=("Segoe UI", 12, "bold"), fg="#ff0000", bg=self.cget('bg'))
        self.rec_label.pack(side="left", padx=(0,10))

        self.time_label = tk.Label(container, text="00:00:00", font=("Segoe UI", 12, "bold"), fg="white", bg=self.cget('bg'))
        self.time_label.pack(side="left", padx=(0,10))
        self.info_label = tk.Label(container, text="Shift+F10 para parar", font=("Segoe UI", 10), fg="white", bg=self.cget('bg'))
        self.info_label.pack(side="left", padx=(0,15))
        self.stop_button = tk.Button(container, text="PARAR", font=("Segoe UI", 9, "bold"), fg="white", bg="#c70000", relief="flat", command=self.recording_module.stop_recording, bd=0, padx=10, pady=2)
        self.stop_button.pack(side="left", padx=(0, 5))
        self.withdraw()

    def _animate_rec(self):
        if not self.winfo_exists() or not self.recording_module.is_recording:
            return
        current_color = self.rec_label.cget("fg")
        new_color = self.cget('bg') if current_color == '#ff0000' else '#ff0000'
        self.rec_label.config(fg=new_color)
        self.animation_id = self.after(700, self._animate_rec)

    def show(self):
        self.update_idletasks()
        x, y = self.master.winfo_screenwidth() - self.winfo_reqwidth() - 20, 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        if self.animation_id is None:
            self._animate_rec()

    def hide(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.animation_id = None
        self.withdraw()

    def update_time(self, elapsed_seconds):
        secs = int(elapsed_seconds)
        mins, secs = divmod(secs, 60)
        hrs, mins = divmod(mins, 60)
        self.time_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
