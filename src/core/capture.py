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
        self.save_path = save_path
        self.overlay_manager = None # Will be instantiated in start_capture_session
        self.capture_indicator = CaptureIndicator(self.root, self)

        # Attributes as per the blueprint
        self.is_in_session = False
        self.screenshots = []
        self.command_bar = None
        self.instruction_label = None
        self.session_counter_label = None
        # The blueprint for transform_command_bar_for_session mentions a button, let's add a placeholder
        self.end_session_button = None

    def start_capture_session(self):
        """Inicia uma nova sessão de captura, limpando qualquer estado anterior."""

        # O FEITIÇO DO RECOMEÇO LIMPO
        # Garante que a lista de troféus da caçada anterior seja esvaziada.
        self.screenshots = []

        if self.is_in_session:
            return
        self.is_in_session = True

        # This part handles displaying overlays on all screens
        self.overlay_manager = PreparationOverlayManager(
            root=self.root,
            indicator=self.capture_indicator,
            indicator_text="Pressione F9 para capturar a tela ativa",
            inactive_text="TELA INATIVA"
        )
        self.overlay_manager.start()

        # This creates the UI on the active screen
        self.create_capture_command_bar()

    def create_capture_command_bar(self):
        """ Creates the command bar UI on the active monitor. """
        active_monitor = self.overlay_manager.get_active_monitor()
        if not active_monitor:
            # Fallback or error
            self.end_capture_session()
            return

        # Create a Toplevel to host the frame, as it's the standard way to make a floating window
        top_level_host = tk.Toplevel(self.root)
        top_level_host.overrideredirect(True)
        top_level_host.wm_attributes("-topmost", True)
        top_level_host.wm_attributes("-alpha", 0.9)

        self.command_bar = tk.Frame(top_level_host, bg="#282c34", pady=5)
        self.command_bar.pack()

        # Initial label as per blueprint
        self.instruction_label = tk.Label(
            self.command_bar,
            text="Mire na tela e pressione F9 para capturar. ESC para encerrar.",
            bg="#282c34", fg="white", font=("Segoe UI", 12)
        )
        self.instruction_label.pack(padx=10, pady=5)

        # Position the UI at the bottom-center of the active monitor
        top_level_host.update_idletasks()
        ui_width = top_level_host.winfo_width()
        x_pos = active_monitor['left'] + (active_monitor['width'] - ui_width) // 2
        y_pos = active_monitor['top'] + active_monitor['height'] - top_level_host.winfo_height() - 20
        top_level_host.geometry(f"+{x_pos}+{y_pos}")


    def take_screenshot(self, active_monitor):
        """ Captures a screenshot of the specified monitor and updates the session. """
        if not self.is_in_session:
            return

        # First Block: Check if it's the first screenshot
        if not self.screenshots:
            self.transform_command_bar_for_session()

        # Second Block: Capture the image
        with mss.mss() as sct:
            sct_img = sct.grab(active_monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # Third Block: Add image to list and update counter
        self.screenshots.append(img)
        self.capture_indicator.update_session_view(len(self.screenshots))
        # The label is guaranteed to exist after the first block
        self.session_counter_label.config(text=f"Total de Capturas: {len(self.screenshots)}")

        # Provide visual feedback (optional, but good UX)
        if self.overlay_manager and self.overlay_manager.indicator:
            self.overlay_manager.indicator.flash_success()

    def transform_command_bar_for_session(self):
        """ Transforms the command bar from initial state to session state. """
        # Destroy the initial instruction label
        if self.instruction_label:
            self.instruction_label.destroy()
            self.instruction_label = None

        # Create and display the new widgets inside the command_bar
        self.session_counter_label = tk.Label(
            self.command_bar,
            text="Total de Capturas: 1", # Initial text
            bg="#282c34", fg="white", font=("Segoe UI", 12)
        )
        self.session_counter_label.pack(side='left', padx=10)

        self.end_session_button = tk.Button(
            self.command_bar,
            text="Encerrar",
            command=self.end_capture_session,
            bg="#5e2927", fg="white", relief="flat", padx=10
        )
        self.end_session_button.pack(side='left', padx=10)


    def end_capture_session(self):
        """ Ends the capture session, cleans up UI, and saves screenshots. """
        if not self.is_in_session:
            return

        self.is_in_session = False

        # Destroy UI elements
        if self.command_bar:
            # The command_bar is inside a Toplevel, so we destroy the Toplevel
            self.command_bar.master.destroy()
            self.command_bar = None # Clear reference
        if self.overlay_manager:
            self.overlay_manager.destroy()
            self.overlay_manager = None

        # Show the main window again if it was hidden
        self.root.deiconify()

        # O FEITIÇO DO ZERAMENTO VISUAL
        # Garante que o placar da caçada seja limpo para o próximo herói.
        if self.capture_indicator:
            self.capture_indicator.reset_view()
            self.capture_indicator.hide()

        # Proceed to save if screenshots were taken
        if not self.screenshots:
            # Limpa a lista mesmo se não houver capturas, para garantir consistência
            self.screenshots = []
            return

        try:
            folder_name_input = simpledialog.askstring(
                "Salvar Sessão de Captura",
                "Digite o nome da pasta para salvar as evidências:",
                parent=self.root
            )
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Sessao_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            session_save_path = os.path.join(self.save_path, base_folder_name)
            os.makedirs(session_save_path, exist_ok=True)

            for i, img in enumerate(self.screenshots):
                filename = f"captura_{i+1:03d}.png"
                full_path = os.path.join(session_save_path, filename)
                img.save(full_path)

            show_success_dialog(
                self.root,
                f"{len(self.screenshots)} captura(s) salva(s) com sucesso!",
                session_save_path,
                session_save_path
            )
        finally:
            # Ensure the list is cleared
            self.screenshots = []
