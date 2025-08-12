import os
from datetime import datetime
from tkinter import simpledialog, messagebox
from PIL import Image
import mss

# Importações corrigidas para a nova estrutura unificada
from ..ui.indicator_widget import IndicatorWidget
from ..ui.dialogs import show_success_dialog, trigger_flash_animation
from ..utils import is_valid_foldername, resource_path # Supondo que resource_path esteja em utils

class ScreenCaptureModule:
    def __init__(self, root, app_config):
        self.root = root
        self.app_config = app_config
        self.indicator = IndicatorWidget(self.root)
        self.is_in_session = False
        self.screenshots = []
        self.overlay_manager = None

    def start_capture_session(self):
        """Inicia uma nova sessão de captura, limpando o estado e mostrando a UI de preparação."""
        # Importação tardia para evitar ciclos de importação, uma boa prática.
        from ..ui.preparation_mode import PreparationOverlayManager
        
        if self.is_in_session:
            return

        print("Iniciando sessão de captura...")
        self.screenshots = []  # Garante que a lista de capturas comece limpa
        self.is_in_session = True
        
        # Cria e inicia o gerenciador de sobreposição, passando a si mesmo como módulo de controle
        self.overlay_manager = PreparationOverlayManager(self.root, self.indicator, self)
        self.overlay_manager.start_capture()

    def take_screenshot(self):
        """Tira um screenshot da tela ativa, adiciona à lista e comanda a atualização do indicador."""
        if not self.is_in_session:
            return

        active_monitor = self.overlay_manager.get_active_monitor()
        if not active_monitor:
            print("Nenhum monitor ativo encontrado para captura.")
            return

        try:
            trigger_flash_animation(self.root)
            with mss.mss() as sct:
                sct_img = sct.grab(active_monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                self.screenshots.append(img)
                print(f"Captura #{len(self.screenshots)} realizada.")
                
                # Comanda o indicador para se transformar/atualizar para o estado de sessão
                self.indicator.update_capture_session(len(self.screenshots), self)

        except Exception as e:
            print(f"Erro de Captura: {e}")

    def end_capture_session(self):
        """Finaliza a sessão de captura, salva os arquivos e limpa a UI."""
        if not self.is_in_session:
            return
            
        print("Encerrando sessão de captura...")
        self.is_in_session = False
        
        # Destrói as sobreposições visuais
        if self.overlay_manager:
            self.overlay_manager.destroy()
            self.overlay_manager = None

        # Procede com o salvamento apenas se houver capturas
        if self.screenshots:
            folder_name_input = simpledialog.askstring(
                "Salvar Evidências", 
                "Digite o nome da pasta para as capturas:", 
                parent=self.root
            )
            
            save_path = self.app_config.get('Paths', 'DefaultSaveLocation')
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencias_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            
            session_save_path = os.path.join(save_path, base_folder_name)
            os.makedirs(session_save_path, exist_ok=True)
            
            for i, img in enumerate(self.screenshots):
                img.save(os.path.join(session_save_path, f"evidencia_{i+1}.png"))
            
            show_success_dialog(
                self.root,
                f"{len(self.screenshots)} captura(s) salva(s) com sucesso!",
                session_save_path,
                session_save_path
            )

        self.screenshots.clear() # Limpa a lista de screenshots para a próxima sessão
