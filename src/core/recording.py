import os
import threading
import time
from datetime import datetime
import cv2
import mss
import numpy as np
from tkinter import messagebox
from ..ui.dialogs import show_success_dialog

# NOTE: The problematic import 'from ..ui.indicator_widget import IndicatorWidget' is removed from here.

class ScreenRecordingModule:
    def __init__(self, root, app_config):
        self.root = root
        self.app_config = app_config

        # LATE IMPORT: This is the fix.
        # The import is moved here to break the circular dependency.
        from ..ui.indicator_widget import IndicatorWidget
        self.indicator = IndicatorWidget(self.root)

        self.is_recording = False
        self.state = "idle" # "idle", "preparing", "recording"
        self.is_preparing = False
        self.save_path = self.app_config.get('Paths', 'DefaultSaveLocation')

        self.out = None
        self.thread = None
        self.target_monitor = None
        self.record_all_screens = False

    def enter_preparation_mode(self, record_all):
        # This method is called from hotkeys and main_window
        # Placeholder implementation
        print(f"Entering preparation mode. Record all: {record_all}")
        self.record_all_screens = record_all
        self.state = "preparing"
        self.is_preparing = True
        # In a real scenario, this would likely involve showing a UI for area selection.
        # For this reconstruction, we'll just change state. The user can then press the hotkey again.
        print("Preparation mode active. Press record hotkey again to start.")

    def start_recording_mode(self):
        # This method is called from hotkeys
        if self.is_recording:
            return
        print("Starting recording...")
        self.is_recording = True
        self.state = "recording"
        self.is_preparing = False
        self.thread = threading.Thread(target=self.recording_thread, daemon=True)
        self.thread.start()

    def stop_recording(self):
        # This method is called from hotkeys
        if not self.is_recording:
            return
        print("Stopping recording...")
        self.is_recording = False
        self.state = "idle"
        # The thread will see the flag and stop itself.

    def exit_preparation_mode(self):
        # This method is called from hotkeys
        print("Exiting preparation mode.")
        self.state = "idle"
        self.is_preparing = False

    def open_recording_selection_ui(self):
        # This method is called from the tray icon
        # Placeholder implementation
        print("Opening recording selection UI...")
        # This would typically open a window or overlay.
        # For now, we can just trigger the preparation mode.
        self.enter_preparation_mode(record_all=False)

    # This is the method that was successfully read from the file.
    def recording_thread(self):
        """A thread que realiza a captura e escrita dos frames de vídeo, sem omissões."""
        
        # --- 1. PREPARAÇÃO DA ÁREA DE CAPTURA E DIMENSÕES ---
        
        capture_area = {}
        width, height = 0, 0

        with mss.mss() as sct:
            if self.record_all_screens:
                print("Modo Onipresente: Calculando dimensões de todas as telas.")
                total_width = sum(m['width'] for m in sct.monitors[1:])
                max_height = max(m['height'] for m in sct.monitors[1:])
                width, height = total_width, max_height
            else:
                print("Modo Focado: Usando dimensões da tela única selecionada.")
                # In a real app, target_monitor would be set during preparation_mode
                if not self.target_monitor:
                    self.target_monitor = sct.monitors[1] # Default to primary monitor
                capture_area = self.target_monitor
                width, height = capture_area['width'], capture_area['height']

        # --- 2. CASCATA DE CONTINGÊNCIA DE CODECS ---
        
        config_parser = self.app_config["config_parser_obj"]
        quality_profile = config_parser.get('Recording', 'quality', fallback='high')
        
        if quality_profile == 'high':
            rec_fps = 15.0
            rec_width, rec_height = width, height
        else: # compact (web)
            rec_fps = 10.0
            aspect_ratio = width / height
            rec_height = 720
            rec_width = int(rec_height * aspect_ratio)

        if rec_width % 2 != 0: rec_width -= 1
        if rec_height % 2 != 0: rec_height -= 1

        filename_base = f"Evidencia_Gravacao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        save_path_dir = self.app_config.get('Paths', 'DefaultSaveLocation')
        self.out = None
        final_video_path = ""

        # NÍVEL 1: Tenta MP4/H.264
        try:
            path = os.path.join(save_path_dir, f"{filename_base}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            self.out = cv2.VideoWriter(path, fourcc, rec_fps, (rec_width, rec_height))
            if not self.out.isOpened(): raise IOError("MP4/avc1 falhou.")
            final_video_path = path
        except Exception:
            self.out = None

        # NÍVEL 2: Tenta WebM/VP9
        if self.out is None:
            try:
                path = os.path.join(save_path_dir, f"{filename_base}.webm")
                fourcc = cv2.VideoWriter_fourcc(*'VP90')
                self.out = cv2.VideoWriter(path, fourcc, rec_fps, (rec_width, rec_height))
                if not self.out.isOpened(): raise IOError("WebM/VP9 falhou.")
                final_video_path = path
            except Exception:
                self.out = None

        # NÍVEL 3: Tenta AVI/MJPG
        if self.out is None:
            try:
                path = os.path.join(save_path_dir, f"{filename_base}.avi")
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                self.out = cv2.VideoWriter(path, fourcc, rec_fps, (rec_width, rec_height))
                if not self.out.isOpened(): raise IOError("AVI/MJPG falhou.")
                final_video_path = path
            except Exception:
                self.out = None
        
        if not self.out or not self.out.isOpened():
            messagebox.showerror("Erro Crítico de Gravação", "Não foi possível iniciar nenhum codec de vídeo.")
            self.root.after(0, self.stop_recording)
            return

        # --- 3. O LOOP PRINCIPAL DE GRAVAÇÃO ---
        with mss.mss() as sct:
            while self.is_recording:
                loop_start_time = time.time()
                try:
                    if self.record_all_screens:
                        monitor = sct.monitors[0]
                        sct_img = sct.grab(monitor)
                        frame_np = np.array(sct_img)
                        final_frame = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)
                    else:
                        sct_img = sct.grab(capture_area)
                        frame_np = np.array(sct_img)
                        final_frame = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)

                    if (final_frame.shape[1], final_frame.shape[0]) != (rec_width, rec_height):
                        frame_to_write = cv2.resize(final_frame, (rec_width, rec_height), interpolation=cv2.INTER_AREA)
                    else:
                        frame_to_write = final_frame

                    self.out.write(frame_to_write)

                    elapsed_time = time.time() - loop_start_time
                    sleep_time = (1.0 / rec_fps) - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                except Exception as e:
                    print(f"Erro no loop de gravação: {e}")
                    self.is_recording = False

        # --- 4. FINALIZAÇÃO ---
        if self.out:
            self.out.release()
        
        if os.path.exists(final_video_path) and os.path.getsize(final_video_path) > 0:
            self.root.after(0, lambda: show_success_dialog(self.root, "Gravação salva!", os.path.dirname(final_video_path), final_video_path))
        
        print("Thread de gravação finalizada.")
