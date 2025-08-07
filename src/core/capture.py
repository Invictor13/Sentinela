import os
import mss
from PIL import Image
from datetime import datetime
from tkinter import simpledialog
from tkinter import Toplevel
import re

from ..ui.capture_indicator import CaptureIndicator
from ..ui.dialogs import show_success_dialog

def is_valid_foldername(name):
    if not name: return False
    if re.search(r'[<>:"/\\|?*]', name): return False
    return True

def trigger_flash_animation(parent_window):
    flash_window = Toplevel(parent_window)
    flash_window.overrideredirect(True)
    flash_window.attributes('-topmost', True)
    try:
        monitor_dims = mss.mss().monitors[1]
    except IndexError:
        monitor_dims = mss.mss().monitors[0]
    flash_window.geometry(f"{monitor_dims['width']}x{monitor_dims['height']}+{monitor_dims['left']}+{monitor_dims['top']}")
    flash_window.attributes('-alpha', 0.0)
    flash_window.configure(bg='white')
    flash_window.attributes('-alpha', 0.3)
    flash_window.after(100, lambda: flash_window.destroy())

class ScreenCaptureModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.capture_indicator = CaptureIndicator(self.root, self)
        self.capturing = False
        self.screenshots = []

    def start_capture_mode(self):
        if self.capturing:
            return
        self.capturing = True
        self.screenshots = []
        self.capture_indicator.update_count(0)
        self.capture_indicator.show()
        self.root.withdraw()

    def take_screenshot(self):
        if self.capturing:
            try:
                trigger_flash_animation(self.root)
                with mss.mss() as sct:
                    sct_img = sct.grab(sct.monitors[0])
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    self.screenshots.append(img)
                self.capture_indicator.update_count(len(self.screenshots))
            except Exception as e:
                print(f"Erro de Captura: {e}")

    def stop_capture_mode(self):
        if not self.capturing:
            return
        self.capturing = False
        self.capture_indicator.hide()
        if self.screenshots:
            folder_name_input = simpledialog.askstring("Salvar Evidências", "Digite o nome da pasta para as capturas:", parent=self.root)
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencias_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            target_save_path = os.path.join(self.save_path, base_folder_name)
            os.makedirs(target_save_path, exist_ok=True)
            for i, img in enumerate(self.screenshots):
                img.save(os.path.join(target_save_path, f"evidencia_{i+1}.png"))
            try:
                os.startfile(target_save_path)
            except Exception as e:
                print(f"Não foi possível abrir a pasta: {e}")
            success_message = f"{len(self.screenshots)} capturas salvas."
            show_success_dialog(self.root, success_message, target_save_path, os.path.abspath(target_save_path))
        self.screenshots.clear()
        self.root.deiconify()
