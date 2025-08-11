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
        self.stop_button = tk.Button(container, text="CONCLUIR", font=("Segoe UI", 9, "bold"), fg="white", bg=COR_BOTAO, relief="flat", command=self.capture_module.end_capture_session, bd=0, padx=10, pady=2)
        self.stop_button.pack(side="left")
        self.stop_button.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_HOVER))
        self.stop_button.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO))
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

    def show_preparation_mode(self, monitor_info, text):
        """Exibe o indicador em um modo de preparação na tela especificada."""
        self.count_label.config(text=text) # Usa o texto dinâmico
        self.stop_button.pack_forget() # Esconde o botão "CONCLUIR" que não faz sentido aqui
        self.update_idletasks()

        # Posiciona a janela no canto superior direito do monitor ativo
        width = self.winfo_reqwidth()
        x = monitor_info['left'] + monitor_info['width'] - width - 20
        y = monitor_info['top'] + 20
        self.geometry(f"+{int(x)}+{int(y)}")

        self.deiconify()

    def flash_success(self):
        """Pisca a cor de fundo para verde para indicar sucesso."""
        original_color = self.cget('bg')
        self.configure(bg="#27ae60") # Verde sucesso
        self.after(200, lambda: self.configure(bg=original_color))

    def hide_preparation_mode(self):
        """Esconde o indicador e restaura o botão 'CONCLUIR' para uso futuro."""
        self.withdraw()
        self.stop_button.pack(side="left") # Garante que o botão esteja visível na próxima vez que o modo normal for usado
