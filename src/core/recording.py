import os
import time
import threading
from datetime import datetime
import cv2
import mss
import numpy as np
from PIL import Image
from pynput.mouse import Controller as MouseController
import tkinter as tk
from tkinter import messagebox
import configparser
from src.config.settings import CONFIG_FILE
from src.utils import resource_path

from src.ui.preparation_indicator import PreparationIndicator
from src.ui.dialogs import show_success_dialog
from src.ui.preparation_mode import PreparationOverlayManager


class ScreenRecordingModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.state = "idle"  # Can be "idle", "preparing", "recording"
        self.out = None
        self.start_time = None
        self.indicator = PreparationIndicator(self.root)
        self.indicator.module_instance = self # For legacy `show` method
        self.sct = mss.mss()
        self.thread_gravacao = None
        self.overlay_manager = None
        self.should_record_all_screens = False

    @property
    def is_recording(self):
        return self.state == "recording"

    @property
    def is_preparing(self):
        return self.state == "preparing"

    def exit_preparation_mode(self):
        if self.state != "preparing":
            return

        if self.overlay_manager:
            self.overlay_manager.destroy()
            self.overlay_manager = None

        self.state = "idle"
        # Ensure the main window is visible again
        self.root.deiconify()

    def enter_preparation_mode(self, record_all_screens=False):
        print(f"[RUNA DE DEPURAÇÃO] Modo de Preparação iniciado com record_all_screens = {record_all_screens}")
        self.should_record_all_screens = record_all_screens
        if self.state != "idle":
            return

        if record_all_screens:
            self.start_recording_mode()
            return

        self.state = "preparing"
        # The overlay manager will hide the root window
        self.overlay_manager = PreparationOverlayManager(
            self.root,
            self.indicator,
            indicator_text="Mire na tela e pressione F10 para Iniciar/Parar",
            inactive_text="Esta tela não será gravada."
        )
        self.overlay_manager.start()

    def start_recording_mode(self, quality_profile="high"):
        active_monitor = None
        if self.state == "preparing":
            if not self.overlay_manager:
                print("Error: In preparing state but no overlay manager found.")
                self.state = "idle"
                return
            active_monitor = self.overlay_manager.get_active_monitor()
            self.overlay_manager.destroy()
            self.overlay_manager = None
        elif self.state != "idle":
            return

        self.state = "recording"
        self.root.withdraw()
        time.sleep(0.2)

        target_monitor = active_monitor if not self.should_record_all_screens else None
        self.thread_gravacao = threading.Thread(target=self.recording_thread, args=(target_monitor, quality_profile), daemon=True)
        self.thread_gravacao.start()

        # The indicator needs to know which monitor to appear on.
        indicator_monitor = active_monitor if active_monitor else self.sct.monitors[1]
        self.indicator.show(indicator_monitor)
        self.start_time = time.time()
        self.update_chronometer_loop()

    def stop_recording(self):
        if self.state == "recording":
            self.state = "idle"
            self.indicator.hide()
            self.root.deiconify()
        elif self.state == "preparing":
            self.state = "idle"
            if self.overlay_manager:
                self.overlay_manager.destroy()
                self.overlay_manager = None
            self.root.deiconify()

    def recording_thread(self, target_to_record, quality_profile):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        quality_profile = config.get('Recording', 'quality', fallback='high')

        filename = os.path.join(self.save_path, f"Evidencia_Gravacao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4")

        try:
            cursor_img = Image.open(resource_path("cursor.png")).convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
        except FileNotFoundError:
            cursor_img = None

        mouse_controller = MouseController()

        if self.should_record_all_screens:
            print("[RUNA DE DEPURAÇÃO] Forja ativada em modo Onipresente (todas as telas).")
            monitors = self.sct.monitors[1:]
            total_width = sum(m['width'] for m in monitors)
            max_height = max(m['height'] for m in monitors)

            if total_width % 2 != 0: total_width += 1
            if max_height % 2 != 0: max_height += 1

            width, height = total_width, max_height
            recording_fps = 15.0
        else:
            if not target_to_record:
                print("Error: Target monitor for recording is not set.")
                self.root.after(0, self.stop_recording)
                return

            original_width, original_height = target_to_record['width'], target_to_record['height']
            if quality_profile == "compact":
                MAX_WIDTH, MAX_HEIGHT = 1280, 720
                recording_fps = 10.0
            else:
                MAX_WIDTH, MAX_HEIGHT = 1920, 1080
                recording_fps = 15.0

            output_width, output_height = original_width, original_height
            if original_width > MAX_WIDTH or original_height > MAX_HEIGHT:
                aspect_ratio = original_width / original_height
                if aspect_ratio > (MAX_WIDTH / MAX_HEIGHT):
                    output_width = MAX_WIDTH
                    output_height = int(output_width / aspect_ratio)
                else:
                    output_height = MAX_HEIGHT
                    output_width = int(output_height * aspect_ratio)

            if output_width % 2 != 0: output_width -= 1
            if output_height % 2 != 0: output_height -= 1
            width, height = output_width, output_height

        codecs_to_try = ['X264', 'avc1', 'mp4v']
        self.out = None
        for codec in codecs_to_try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            try:
                self.out = cv2.VideoWriter(filename, fourcc, recording_fps, (width, height))
                if self.out.isOpened(): break
            except Exception: self.out = None

        if not self.out or not self.out.isOpened():
            messagebox.showerror("Erro Crítico", "Nenhum codec de vídeo funcional foi encontrado.")
            self.root.after(0, self.stop_recording)
            return

        # ANTES do loop, garanta que o indicador esteja visível.
        self.indicator.deiconify()

        with mss.mss() as sct:
            while self.is_recording:
                loop_start_time = time.time()
                try:
                    if self.should_record_all_screens:
                        monitors_to_capture = sct.monitors[1:]
                        combined_frame = np.zeros((height, width, 3), dtype=np.uint8)
                        current_x_offset = 0
                        virtual_screen_left = sct.monitors[0]['left']
                        virtual_screen_top = sct.monitors[0]['top']

                        for monitor in monitors_to_capture:
                            sct_img = sct.grab(monitor)
                            frame_np = np.array(sct_img)
                            h_m, w_m, _ = frame_np.shape
                            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)
                            combined_frame[0:h_m, current_x_offset:current_x_offset + w_m] = frame_bgr
                            current_x_offset += w_m

                        final_frame_pil = Image.fromarray(cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB))
                        if cursor_img:
                            mouse_pos = mouse_controller.position
                            cursor_x = mouse_pos[0] - virtual_screen_left
                            cursor_y = mouse_pos[1] - virtual_screen_top
                            final_frame_pil.paste(cursor_img, (cursor_x, cursor_y), cursor_img)
                        self.out.write(cv2.cvtColor(np.array(final_frame_pil), cv2.COLOR_RGB2BGR))
                    else:
                        capture_area = target_to_record

                        sct_img = sct.grab(capture_area)

                        frame_np = np.array(sct_img)
                        original_width, original_height = target_to_record['width'], target_to_record['height']
                        if (original_width, original_height) != (width, height):
                            frame_np_resized = cv2.resize(frame_np, (width, height), interpolation=cv2.INTER_AREA)
                        else:
                            frame_np_resized = frame_np
                        frame_pil = Image.fromarray(cv2.cvtColor(frame_np_resized, cv2.COLOR_BGRA2RGB))
                        if cursor_img:
                            mouse_pos = mouse_controller.position
                            cursor_x_in_capture = mouse_pos[0] - capture_area['left']
                            cursor_y_in_capture = mouse_pos[1] - capture_area['top']
                            scaled_cursor_x = int(cursor_x_in_capture * (width / original_width))
                            scaled_cursor_y = int(cursor_y_in_capture * (height / original_height))
                            frame_pil.paste(cursor_img, (scaled_cursor_x, scaled_cursor_y), cursor_img)
                        self.out.write(cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR))
                except Exception as e:
                    print(f"Erro durante o loop de gravação: {e}")
                    if self.indicator:
                        self.indicator.deiconify()
                    self.state = "idle"
                sleep_time = (1/recording_fps) - (time.time() - loop_start_time)
                if sleep_time > 0: time.sleep(sleep_time)

        # DEPOIS do loop, esconda o indicador
        self.indicator.hide()
        if self.out: self.out.release()
        def finalize_on_main_thread():
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                show_success_dialog(self.root, "Gravação salva.", os.path.dirname(filename), filename)
            elif os.path.exists(filename):
                os.remove(filename)
        self.root.after(0, finalize_on_main_thread)

    def update_chronometer_loop(self):
        if self.is_recording and self.start_time is not None:
            self.indicator.update_time(time.time() - self.start_time)
            self.root.after(1000, self.update_chronometer_loop)
