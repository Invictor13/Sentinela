import tkinter as tk
from tkinter import Toplevel

COR_BOTAO = "#00995D"
COR_BOTAO_HOVER = "#007a4a"

class CaptureIndicator(Toplevel):
    def __init__(self, parent, capture_module):
        super().__init__(parent)
        self.capture_module = capture_module
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg='#2b2b2b')
        container = tk.Frame(self, bg=self.cget('bg'))
        container.pack(padx=10, pady=5)
        self.count_label = tk.Label(container, text="Capturas: 0", font=("Segoe UI", 12, "bold"), fg="white", bg=self.cget('bg'))
        self.count_label.pack(side="left", padx=(0,15))
        info_label = tk.Label(container, text="Pressione Shift+F9 para capturar", font=("Segoe UI", 10), fg="#cccccc", bg=self.cget('bg'))
        info_label.pack(side="left", padx=(0,15))
        stop_button = tk.Button(container, text="CONCLUIR", font=("Segoe UI", 9, "bold"), fg="white", bg=COR_BOTAO, relief="flat", command=self.capture_module.end_capture_session, bd=0, padx=10, pady=2)
        stop_button.pack(side="left")
        stop_button.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_HOVER))
        stop_button.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO))
        self.withdraw()

    def show(self):
        self.update_idletasks()
        parent_width = self.master.winfo_screenwidth()
        width = self.winfo_reqwidth()
        x, y = parent_width - width - 20, 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()

    def update_count(self, count):
        self.count_label.config(text=f"Capturas: {count}")
