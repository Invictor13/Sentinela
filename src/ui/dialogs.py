import tkinter as tk
from tkinter import Toplevel

COR_FUNDO_JANELA = "#f0f5f0"
COR_TEXTO_PRINCIPAL = "#005a36"
COR_TEXTO_SECUNDARIO = "#555555"
COR_BOTAO = "#00995D"

def show_success_dialog(root, message, folder_path, specific_path_to_copy):
    dialog = Toplevel(root)
    dialog.title("Sucesso")
    dialog.configure(bg=COR_FUNDO_JANELA)
    dialog.resizable(False, False)
    dialog.wm_attributes("-topmost", True)
    root.update_idletasks()
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    dialog_width, dialog_height = 450, 220
    x = (screen_width // 2) - (dialog_width // 2)
    y = (screen_height // 2) - (dialog_height // 2)
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    tk.Label(dialog, text="Operação Concluída com Sucesso!", font=("Segoe UI", 12, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(pady=(20, 10))
    tk.Label(dialog, text=f"A pasta de destino já foi aberta.\n{message}", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO, wraplength=430).pack()

    button_frame = tk.Frame(dialog, bg=COR_FUNDO_JANELA)
    button_frame.pack(pady=20, expand=True)

    def copy_path_action():
        dialog.clipboard_clear()
        dialog.clipboard_append(specific_path_to_copy)
        copy_button.config(text="Copiado!", state=tk.DISABLED)
        dialog.after(1500, lambda: copy_button.config(text="Copiar Caminho", state=tk.NORMAL))
    copy_button = tk.Button(button_frame, text="Copiar Caminho", command=copy_path_action, font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=10, pady=5)
    copy_button.pack(side="left", padx=5)

    close_button = tk.Button(button_frame, text="Concluir", command=dialog.destroy, font=("Segoe UI", 10), relief=tk.FLAT, padx=10, pady=5)
    close_button.pack(side="left", padx=5)
    close_button.focus_set()

    dialog.after(7000, dialog.destroy)


class WelcomeWindow(Toplevel):
    def __init__(self, parent, on_close_callback):
        super().__init__(parent)
        self.on_close_callback = on_close_callback

        self.title("Bem-Vindo ao Sentinela!")
        self.geometry("550x350")
        self.configure(bg=COR_FUNDO_JANELA)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.wm_attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        main_frame = tk.Frame(self, bg=COR_FUNDO_JANELA, padx=25, pady=20)
        main_frame.pack(expand=True, fill="both")

        tk.Label(main_frame, text="Olá! Parece que esta é a sua primeira vez aqui.", font=("Segoe UI", 14, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(pady=(0, 15))

        info_text = (
            "Para começar, aqui estão 3 funcionalidades chave que você pode configurar:\n\n"
            "1. Local dos Arquivos: Você pode escolher exatamente onde salvar suas evidências na tela de Configurações.\n\n"
            "2. Qualidade dos Vídeos: Escolha entre 'Full HD' para máxima qualidade ou 'Web (720p)' para arquivos mais leves e fáceis de compartilhar.\n\n"
            "3. Seus Atalhos: Os atalhos padrão são F9 (Captura) e F10 (Gravação), mas você pode personalizá-los como quiser na tela de Configurações!"
        )

        tk.Label(main_frame, text=info_text, font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO, justify="left", wraplength=500).pack(pady=(0, 20))

        ok_button = tk.Button(main_frame, text="Entendi, vamos começar!", command=self.on_close, font=("Segoe UI", 11, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=10, pady=5)
        ok_button.pack()

    def on_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()
