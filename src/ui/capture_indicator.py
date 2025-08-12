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

        # --- Widgets Dinâmicos ---
        # 1. Rótulo de instrução inicial (visível por padrão)
        self.instruction_label = tk.Label(container, text="Pressione F9 para capturar a Tela Ativa", font=("Segoe UI", 10), fg="#cccccc", bg=self.cget('bg'))
        self.instruction_label.pack(side="left", padx=(0, 15))

        # 2. Rótulo do contador (inicialmente oculto)
        self.counter_label = tk.Label(container, font=("Segoe UI", 12, "bold"), fg="white", bg=self.cget('bg'))

        # 3. Botão de encerrar (inicialmente oculto)
        self.end_button = tk.Button(container, text="Encerrar", font=("Segoe UI", 9, "bold"), fg="white", bg=COR_BOTAO, relief="flat", command=self.capture_module.end_capture_session, bd=0, padx=10, pady=2)
        self.end_button.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_HOVER))
        self.end_button.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO))

        self.withdraw()

    def update_session_view(self, count):
        """Atualiza a UI do indicador com base no número de capturas."""
        if count == 1:
            # Primeira captura: transforma a UI
            self.instruction_label.pack_forget()
            self.counter_label.pack(side="left", padx=(0, 15))
            self.end_button.pack(side="left")

        # Atualiza o texto do contador em todas as chamadas
        self.counter_label.config(text=f"Total de Capturas: {count}")

    def reset_view(self):
        """Redefine o indicador para o seu estado inicial."""
        self.counter_label.pack_forget()
        self.end_button.pack_forget()
        self.instruction_label.pack(side="left", padx=(0, 15))
        self.instruction_label.config(text="Pressione F9 para capturar a Tela Ativa")


    def show(self):
        self.update_idletasks()
        parent_width = self.master.winfo_screenwidth()
        width = self.winfo_reqwidth()
        x, y = parent_width - width - 20, 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        self.withdraw()

    def show_preparation_mode(self, monitor_info, text):
        """Exibe o indicador em um modo de preparação na tela especificada."""
        self.instruction_label.config(text=text) # Reutiliza o label de instrução para o modo de preparação
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
        """Esconde o indicador de preparação."""
        self.withdraw()
