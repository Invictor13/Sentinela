import os
import mss
import tkinter as tk
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
        self.indicator = PreparationIndicator(self.root)
        self.overlay_manager = None

        # Session state
        self.is_in_session = False
        self.screenshots = []

        # Session UI
        self.session_ui = None
        self.main_frame = None
        self.instruction_label = None
        self.counter_label = None
        self.end_button = None
        self.esc_hint_label = None

    def start_capture_session(self):
        if self.is_in_session:
            return

        self.is_in_session = True
        self.screenshots = []

        self.overlay_manager = PreparationOverlayManager(
            self.root,
            self.indicator,
            indicator_text="Pressione F9 para capturar a tela ativa",
            inactive_text="ESTA TELA NÃO ESTÁ SENDO GRAVADA..."
        )
        self.overlay_manager.start()
        self._create_session_ui()

    def _create_session_ui(self):
        active_monitor = self.overlay_manager.get_active_monitor()
        if not active_monitor:
            return

        self.session_ui = tk.Toplevel(self.root)
        self.session_ui.overrideredirect(True)
        self.session_ui.wm_attributes("-topmost", True)
        self.session_ui.wm_attributes("-alpha", 0.9)

        bg_color, fg_color, font_family = "#282c34", "white", "Segoe UI"

        self.main_frame = tk.Frame(self.session_ui, bg=bg_color)
        self.main_frame.pack(fill="both", expand=True)

        # --- Create all widgets upfront ---

        # 1. Preparation-phase widget
        self.instruction_label = tk.Label(
            self.main_frame,
            text="Mire na tela e pressione F9 para capturar. Pressione ESC para sair.",
            bg=bg_color, fg=fg_color, font=(font_family, 12)
        )

        # 2. Capture-phase widgets
        self.end_button = tk.Button(
            self.main_frame, text="CONCLUIR SESSÃO", command=self.end_capture_session,
            bg="red", fg="white", font=(font_family, 10, "bold"), relief="flat", padx=10
        )
        self.esc_hint_label = tk.Label(
            self.main_frame, text="(ou pressione ESC)",
            bg=bg_color, fg=fg_color, font=(font_family, 9)
        )
        self.counter_label = tk.Label(
            self.main_frame, text="Capturas: 0",
            bg=bg_color, fg=fg_color, font=(font_family, 12)
        )

        # --- Initial layout ---
        # Only show the instruction label initially
        self.instruction_label.pack(padx=10, pady=10)

        # Positioning the UI
        self.session_ui.update_idletasks()
        ui_width = self.session_ui.winfo_width()
        x_pos = active_monitor['left'] + (active_monitor['width'] - ui_width) // 2
        y_pos = active_monitor['top'] + active_monitor['height'] - self.session_ui.winfo_height() - 20
        self.session_ui.geometry(f"+{x_pos}+{y_pos}")

    def _transition_to_capture_ui(self):
        """Hides preparation widgets and shows capture-in-progress widgets."""
        # Hide preparation UI
        self.instruction_label.pack_forget()

        # Show capture UI (pack order matters for layout)
        self.end_button.pack(side="right", padx=(0, 10), pady=5)
        self.esc_hint_label.pack(side="right", padx=(0, 5))
        self.counter_label.pack(side="left", padx=10, pady=5)


    def end_capture_session(self):
        if not self.is_in_session:
            return

        # Destroy UI elements first
        if self.overlay_manager:
            self.overlay_manager.destroy()
            self.overlay_manager = None
        if self.session_ui:
            self.session_ui.destroy()
            self.session_ui = None

        self.is_in_session = False
        self.root.deiconify() # Show the main window again

        # Proceed to save if screenshots were taken
        if not self.screenshots:
            return # No need to ask for folder name if nothing was captured

        try:
            folder_name_input = simpledialog.askstring(
                "Salvar Evidências",
                "Digite o nome da pasta para esta sessão de capturas:",
                parent=self.root
            )
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencia_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            session_save_path = os.path.join(self.save_path, base_folder_name)
            os.makedirs(session_save_path, exist_ok=True)

            for i, img in enumerate(self.screenshots):
                filename = f"captura_{i+1:03d}_{datetime.now().strftime('%H%M%S')}.png"
                full_path = os.path.join(session_save_path, filename)
                img.save(full_path)

            show_success_dialog(
                self.root,
                f"{len(self.screenshots)} captura(s) salva(s) com sucesso!",
                session_save_path
            )
        finally:
            # Ensure screenshots list is cleared even if user cancels the dialog
            self.screenshots = []


    def take_screenshot(self, monitor):
        if not self.is_in_session:
            return

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            self.screenshots.append(img)

            # Transition UI on first screenshot
            if len(self.screenshots) == 1:
                self._transition_to_capture_ui()

            # Update UI counter
            if self.counter_label:
                self.counter_label.config(text=f"Capturas: {len(self.screenshots)}")

            # Flash indicator for visual feedback
            if self.overlay_manager and self.overlay_manager.indicator:
                self.overlay_manager.indicator.flash_success()

        except Exception as e:
            print(f"Erro de Captura: {e}")
