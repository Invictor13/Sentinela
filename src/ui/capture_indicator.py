import tkinter as tk
from tkinter import Toplevel

COR_BOTAO = "#00995D"
COR_BOTAO_HOVER = "#007a4a"

class CaptureIndicator(tk.Toplevel):
    def __init__(self, parent, capture_module):
        super().__init__(parent)
        self.capture_module = capture_module
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg='#2b2b2b')

        # --- Container Principal ---
        container = tk.Frame(self, bg=self.cget('bg'))
        container.pack(padx=10, pady=5)

        # --- Widgets para TODOS os estados ---
        # Serão mostrados ou escondidos conforme a necessidade

        # Estado 1: Instrução Inicial
        self.instruction_label = tk.Label(
            container,
            text="Pressione F9 para capturar a tela ativa",
            font=("Segoe UI", 10),
            fg="#cccccc",
            bg=self.cget('bg')
        )

        # Estado 2: Sessão de Captura Ativa (agrupados em um frame)
        self.session_frame = tk.Frame(container, bg=self.cget('bg'))
        
        self.counter_label = tk.Label(
            self.session_frame,
            text="Capturas: 0",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg=self.cget('bg')
        )
        self.counter_label.pack(side="left", padx=(0, 10))

        self.end_button = tk.Button(
            self.session_frame,
            text="CONCLUIR",
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg="#c0392b",
            relief="flat",
            command=self.capture_module.end_capture_session,
            bd=0,
            padx=10,
            pady=2
        )
        self.end_button.pack(side="left")

        self.esc_label = tk.Label(
            self.session_frame,
            text="(ou ESC)",
            font=("Segoe UI", 8),
            fg="#cccccc",
            bg=self.cget('bg')
        )
        self.esc_label.pack(side="left", padx=(5, 0))
        
        self.withdraw() # O indicador sempre começa escondido

    def show_initial_state(self, monitor_info):
        """Mostra o indicador no estado inicial de preparação."""
        self.session_frame.pack_forget() # Garante que o frame da sessão esteja oculto
        self.instruction_label.pack() # Mostra a instrução
        self._position_and_show(monitor_info)

    def update_session_view(self, count):
        """Transforma ou atualiza o indicador para o modo de sessão."""
        self.instruction_label.pack_forget() # Garante que a instrução esteja oculta
        self.session_frame.pack() # Mostra o frame da sessão
        self.counter_label.config(text=f"Capturas: {count}")

    def hide(self):
        """Esconde o indicador completamente."""
        self.withdraw()

    def _position_and_show(self, monitor_info):
        """Lógica interna para posicionar e exibir a janela."""
        self.update_idletasks()
        parent_width = self.master.winfo_screenwidth()
        width = self.winfo_reqwidth()
        # Posiciona no canto superior direito do monitor ativo
        x = monitor_info['left'] + monitor_info['width'] - width - 20
        y = monitor_info['top'] + 20
        self.geometry(f"+{int(x)}+{int(y)}")
        self.deiconify()
