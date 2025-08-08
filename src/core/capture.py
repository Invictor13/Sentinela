import os
import mss
from PIL import Image
from datetime import datetime
from tkinter import simpledialog
import re

from ..ui.preparation_indicator import PreparationIndicator
from ..ui.preparation_mode import PreparationOverlayManager
from ..ui.dialogs import show_success_dialog

def is_valid_foldername(name):
    if not name: return False
    if re.search(r'[<>:"/\\|?*]', name): return False
    return True

class ScreenCaptureModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.is_preparing = False
        self.overlay_manager = None
        # The indicator is created here but used by the overlay manager
        self.indicator = PreparationIndicator(self.root)

    def enter_preparation_mode(self):
        if self.is_preparing:
            return

        self.is_preparing = True
        self.overlay_manager = PreparationOverlayManager(
            self.root,
            self.indicator,
            indicator_text="Mire na tela e pressione F9 para Capturar",
            inactive_text="Esta tela não será capturada"
        )
        self.overlay_manager.start()

    def exit_preparation_mode(self):
        if not self.is_preparing:
            return

        if self.overlay_manager:
            self.overlay_manager.destroy()
            self.overlay_manager = None

        self.is_preparing = False
        self.root.deiconify()

    def take_screenshot(self, monitor):
        if not self.is_preparing:
            return

        try:
            # The overlay manager is destroyed after the screenshot is taken
            with mss.mss() as sct:
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # --- Save the single screenshot ---
            folder_name_input = simpledialog.askstring(
                "Salvar Evidência",
                "Digite o nome da pasta para a captura:",
                parent=self.root
            )
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencia_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            target_save_path = os.path.join(self.save_path, base_folder_name)
            os.makedirs(target_save_path, exist_ok=True)

            filename = f"captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
            full_path = os.path.join(target_save_path, filename)
            img.save(full_path)

            show_success_dialog(
                self.root,
                "Captura salva com sucesso!",
                target_save_path,
                os.path.abspath(full_path)
            )

        except Exception as e:
            print(f"Erro de Captura: {e}")
        finally:
            # Ensure we always exit preparation mode
            self.exit_preparation_mode()
