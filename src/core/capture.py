import os
import mss
import tkinter as tk
from PIL import Image
from datetime import datetime
from tkinter import simpledialog
import re

# Assuming these are the correct locations from the original file
from src.ui.preparation_mode import PreparationOverlayManager
from src.ui.dialogs import show_success_dialog
from src.ui.capture_indicator import CaptureIndicator

def is_valid_foldername(name):
    """ Helper function to validate folder names. """
    if not name: return False
    # Windows reserved characters
    if re.search(r'[<>:"/\\|?*]', name): return False
    return True

class ScreenCaptureModule:
    def __init__(self, root, save_path):
        self.root = root
        self.default_save_path = save_path
        self.capture_indicator = CaptureIndicator(self.root, self)
        self.is_in_session = False
        self.screenshots = []
        self.overlay_manager = None # Supondo que o overlay é gerenciado aqui

    def start_capture_session(self):
        """Inicia uma nova sessão de captura, limpando o estado e mostrando a UI."""
        from ..ui.preparation_mode import PreparationOverlayManager # Importação tardia para evitar ciclos
        
        if self.is_in_session:
            return

        print("Iniciando sessão de captura...")
        self.screenshots = []
        self.is_in_session = True
        
        self.overlay_manager = PreparationOverlayManager(self.root, self.capture_indicator, "Pressione F9 para capturar a tela ativa")
        self.overlay_manager.start()

    def take_screenshot(self, active_monitor):
        """Tira um screenshot da tela ativa e comanda a atualização do indicador."""
        if not self.is_in_session:
            return

        if not active_monitor:
            return

        try:
            trigger_flash_animation(self.root)
            with mss.mss() as sct:
                sct_img = sct.grab(active_monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                self.screenshots.append(img)
                print(f"Captura #{len(self.screenshots)} realizada.")
                
                # Comanda o indicador para se transformar/atualizar
                self.capture_indicator.update_session_view(len(self.screenshots))

        except Exception as e:
            print(f"Erro de Captura: {e}")

    def end_capture_session(self):
        """Finaliza a sessão, salva os arquivos e limpa tudo."""
        if not self.is_in_session:
            return
            
        print("Encerrando sessão de captura...")
        self.is_in_session = False
        
        if self.overlay_manager:
            self.overlay_manager.destroy()
            self.overlay_manager = None

        if self.screenshots:
            folder_name_input = simpledialog.askstring("Salvar Evidências", "Digite o nome da pasta para as capturas:", parent=self.root)
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencias_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            
            session_save_path = os.path.join(self.default_save_path, base_folder_name)
            os.makedirs(session_save_path, exist_ok=True)
            
            for i, img in enumerate(self.screenshots):
                img.save(os.path.join(session_save_path, f"evidencia_{i+1}.png"))
            
            # Supondo que show_success_dialog espera 4 argumentos
            show_success_dialog(
                self.root,
                f"{len(self.screenshots)} captura(s) salva(s) com sucesso!",
                session_save_path,
                session_save_path
            )

        self.screenshots.clear()
