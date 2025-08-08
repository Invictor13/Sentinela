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
        self.indicator = PreparationIndicator(self.root)
        # Session-specific attributes for multi-capture
        self.session_save_path = None
        self.session_capture_count = 0

    def enter_preparation_mode(self):
        if self.is_preparing:
            return

        # Reset session state at the beginning of a new preparation
        self.session_save_path = None
        self.session_capture_count = 0

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

        # Show a summary dialog if screenshots were taken in this session
        if self.session_capture_count > 0 and self.session_save_path:
            show_success_dialog(
                self.root,
                f"{self.session_capture_count} captura(s) salva(s) com sucesso!",
                self.session_save_path
            )

    def take_screenshot(self, monitor):
        if not self.is_preparing:
            return

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # --- Folder Management for the Session ---
            # Ask for folder name only on the first capture of the session
            if not self.session_save_path:
                folder_name_input = simpledialog.askstring(
                    "Salvar Evidências",
                    "Digite o nome da pasta para esta sessão de capturas:",
                    parent=self.root
                )
                base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencia_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
                self.session_save_path = os.path.join(self.save_path, base_folder_name)
                os.makedirs(self.session_save_path, exist_ok=True)

            # --- Save the screenshot ---
            self.session_capture_count += 1
            filename = f"captura_{self.session_capture_count:03d}_{datetime.now().strftime('%H%M%S')}.png"
            full_path = os.path.join(self.session_save_path, filename)
            img.save(full_path)

            # Optionally, give some visual feedback that a capture was taken
            # For example, flash the indicator
            if self.overlay_manager and self.overlay_manager.indicator:
                self.overlay_manager.indicator.flash_success()


        except Exception as e:
            print(f"Erro de Captura: {e}")
