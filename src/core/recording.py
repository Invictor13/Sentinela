import os
import time
import threading
from datetime import datetime
import cv2
import mss
import numpy as np
from PIL import Image, ImageTk
from pynput.mouse import Controller as MouseController
import tkinter as tk
from tkinter import Toplevel, messagebox
from pynput.mouse import Controller as MouseController

from ..ui.recording_indicator import RecordingIndicator
from ..ui.dialogs import show_success_dialog


class ScreenRecordingModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.state = "idle"  # Can be "idle", "preparing", "recording"
        self.out = None
        self.start_time = None
        self.recording_indicator = RecordingIndicator(self.root, self)
        self.sct = mss.mss()
        self.thread_gravacao = None
        self.preparation_overlays = []
        self.active_monitor_for_recording = None

    @property
    def is_recording(self):
        return self.state == "recording"

    def enter_preparation_mode(self):
        if self.state != "idle":
            return
        self.state = "preparing"
        self.root.withdraw()

        mouse_pos = MouseController().position
        monitors = self.sct.monitors[1:]
        self.active_monitor_for_recording = None

        for m in monitors:
            if m['left'] <= mouse_pos[0] < m['left'] + m['width'] and \
               m['top'] <= mouse_pos[1] < m['top'] + m['height']:
                self.active_monitor_for_recording = m
                break

        if not self.active_monitor_for_recording and monitors:
            self.active_monitor_for_recording = monitors[0]

        for monitor in monitors:
            if monitor == self.active_monitor_for_recording:
                self.recording_indicator.show_preparation_mode()
            else:
                self._create_inactive_overlay(monitor)

    def _create_inactive_overlay(self, monitor):
        overlay = Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
        overlay.wm_attributes("-topmost", True)
        overlay.wm_attributes("-alpha", 0.7)

        canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        w, h = monitor['width'], monitor['height']
        try:
            # Efeito de ruído estático para diferenciar
            tile_size = 128
            noise = np.random.randint(0, 25, (tile_size, tile_size), dtype=np.uint8)
            noise_pil = Image.fromarray(noise, 'L')
            full_img = Image.new('L', (w, h))
            for y_pos in range(0, h, tile_size):
                for x_pos in range(0, w, tile_size):
                    full_img.paste(noise_pil, (x_pos, y_pos))

            noise_tk = ImageTk.PhotoImage(full_img)
            canvas.create_image(0, 0, image=noise_tk, anchor="nw")
            overlay.noise_ref = noise_tk
        except Exception as e:
            print(f"Falha ao criar efeito de ruído para overlay: {e}")

        try:
            logo_image = Image.open("assets/logo.png").resize((120, 120), Image.Resampling.LANCZOS)
            logo_tk = ImageTk.PhotoImage(logo_image)
            canvas.create_image(w/2, h/2 - 50, image=logo_tk)
            overlay.logo_ref = logo_tk
        except Exception as e:
            print(f"Não foi possível carregar o logo para a sobreposição: {e}")

        canvas.create_text(w/2, h/2 + 40, text="Esta tela não será gravada.",
                            fill="white", font=("Segoe UI", 16, "bold"), justify="center")

        self.preparation_overlays.append(overlay)

    def _destroy_preparation_overlays(self):
        for overlay in self.preparation_overlays:
            overlay.destroy()
        self.preparation_overlays = []

    def start_recording_mode(self, quality_profile="high"):
        if self.state != "preparing":
            return

        self._destroy_preparation_overlays()
        self.state = "recording"
        time.sleep(0.2)

        self.thread_gravacao = threading.Thread(target=self.recording_thread, args=(self.active_monitor_for_recording, quality_profile), daemon=True)
        self.thread_gravacao.start()

        self.recording_indicator.show() # Transita para o modo de gravação
        self.start_time = time.time()
        self.update_chronometer_loop()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.state = "idle"
        self.recording_indicator.hide()
        self.root.deiconify()

    def recording_thread(self, target_to_record, quality_profile):
        # A gravação é sempre de um monitor inteiro, então is_window_recording é falso.
        is_window_recording = False

        if is_window_recording:
            original_width, original_height = target_to_record.width, target_to_record.height
        else:
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
            print(f"Alerta: Resolução original ({original_width}x{original_height}) redimensionada para ({output_width}x{output_height}) para otimização.")

        if output_width % 2 != 0:
            output_width -= 1
        if output_height % 2 != 0:
            output_height -= 1

        width, height = output_width, output_height

        filename = os.path.join(self.save_path, f"Evidencia_Gravacao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4")

        codecs_to_try = ['X264', 'avc1', 'mp4v']
        self.out = None

        for codec in codecs_to_try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            try:
                self.out = cv2.VideoWriter(filename, fourcc, recording_fps, (width, height))
                if self.out.isOpened():
                    print(f"Sucesso: Codec '{codec}' invocado com sucesso a {recording_fps} FPS.")
                    break
            except Exception:
                self.out = None

        if not self.out or not self.out.isOpened():
            messagebox.showerror("Erro Crítico", "Nenhum codec de vídeo funcional foi encontrado. A gravação foi abortada.")
            self.root.after(0, self.stop_recording)
            return

        try:
            cursor_img = Image.open("assets/cursor.png").convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
        except FileNotFoundError:
            cursor_img = None
        mouse_controller = MouseController()
        with mss.mss() as sct:
            while self.is_recording:
                loop_start_time = time.time()
                try:
                    if is_window_recording:
                        if not target_to_record.visible or target_to_record.isMinimized:
                            self.is_recording = False
                            continue
                        capture_area = {'top': target_to_record.top, 'left': target_to_record.left, 'width': original_width, 'height': original_height}
                    else:
                        capture_area = target_to_record

                    sct_img = sct.grab(capture_area)
                    frame_np = np.array(sct_img)

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
                    self.is_recording = False

                sleep_time = (1/recording_fps) - (time.time() - loop_start_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        if self.out:
            self.out.release()

        def finalize_on_main_thread():
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                show_success_dialog(self.root, "Gravação salva.", os.path.dirname(filename), filename)
            elif os.path.exists(filename):
                os.remove(filename)

        self.root.after(0, finalize_on_main_thread)

    def update_chronometer_loop(self):
        if self.is_recording and self.start_time is not None:
            self.recording_indicator.update_time(time.time() - self.start_time)
            self.root.after(1000, self.update_chronometer_loop)
