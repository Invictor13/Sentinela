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
import configparser
from ..config.settings import CONFIG_FILE

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

        # --- NEW: Attributes for dynamic focus and animation ---
        self.preparation_overlays = {}  # Dict to map monitor_id to overlay info
        self.active_monitor_for_recording = None
        self.focus_check_id = None # ID for the focus checking loop
        # No need for self.animation_ids, it will be handled inside the overlay_info dict
        # --- END NEW ---

    @property
    def is_recording(self):
        return self.state == "recording"

    # --- MODIFIED: enter_preparation_mode ---
    def enter_preparation_mode(self, record_all_screens=False):
        if self.state != "idle":
            return

        if record_all_screens:
            # Bypassa o modo de preparação e inicia a gravação diretamente
            self.start_recording_mode(record_all_screens=True)
            return

        self.state = "preparing"
        self.root.withdraw()

        mouse_pos = MouseController().position
        # We add a unique ID to each monitor dictionary
        monitors = [{**m, 'id': i} for i, m in enumerate(self.sct.monitors[1:])]

        # Determine initial active monitor
        initial_active_monitor = None
        for m in monitors:
            if m['left'] <= mouse_pos[0] < m['left'] + m['width'] and \
               m['top'] <= mouse_pos[1] < m['top'] + m['height']:
                initial_active_monitor = m
                break

        if not initial_active_monitor and monitors:
            initial_active_monitor = monitors[0]

        self.active_monitor_for_recording = initial_active_monitor

        # Create overlays for all monitors
        for monitor in monitors:
            if monitor['id'] == self.active_monitor_for_recording['id']:
                # Active monitor gets the preparation indicator
                self.recording_indicator.show_preparation_mode(monitor)
            else:
                # Inactive monitors get the dark, noisy overlay
                self._create_inactive_overlay(monitor)

        # Start tracking mouse movement
        self.focus_check_id = self.root.after(250, self.update_active_screen_focus)

    # --- NEW: update_active_screen_focus ---
    def update_active_screen_focus(self):
        if self.state != "preparing":
            return # Stop loop if not in preparation mode

        mouse_pos = MouseController().position
        monitors = [{**m, 'id': i} for i, m in enumerate(self.sct.monitors[1:])]

        new_active_monitor = None
        for m in monitors:
            if m['left'] <= mouse_pos[0] < m['left'] + m['width'] and \
               m['top'] <= mouse_pos[1] < m['top'] + m['height']:
                new_active_monitor = m
                break

        if new_active_monitor and new_active_monitor['id'] != self.active_monitor_for_recording['id']:
            self.swap_focus(new_active_monitor)

        # Reschedule the check
        self.focus_check_id = self.root.after(250, self.update_active_screen_focus)

    # --- NEW: swap_focus ---
    def swap_focus(self, new_monitor):
        old_monitor = self.active_monitor_for_recording

        # Deactivate the old monitor: hide indicator and create inactive overlay
        self.recording_indicator.hide_preparation_mode()
        self._create_inactive_overlay(old_monitor)

        # Activate the new monitor: destroy inactive overlay and show indicator
        if new_monitor['id'] in self.preparation_overlays:
            overlay_info = self.preparation_overlays.pop(new_monitor['id'])
            if overlay_info['animation_id']:
                self.root.after_cancel(overlay_info['animation_id'])
            overlay_info['window'].destroy()

        self.active_monitor_for_recording = new_monitor
        self.recording_indicator.show_preparation_mode(new_monitor)

    # --- NEW: animate_static_effect ---
    def animate_static_effect(self, monitor_id):
        if self.state != "preparing" or monitor_id not in self.preparation_overlays:
            return

        overlay_info = self.preparation_overlays[monitor_id]
        canvas = overlay_info['canvas']
        image_item = overlay_info['image_item']

        if not canvas.winfo_exists() or not image_item:
            return

        w, h = overlay_info['window'].winfo_width(), overlay_info['window'].winfo_height()
        if w == 1 or h == 1: # Window might not be sized yet
            self.root.after(50, self.animate_static_effect, monitor_id)
            return

        try:
            tile_size = 128
            # Generate a smaller noise pattern and tile it, which is more performant
            noise_pattern = np.random.randint(0, 35, (tile_size, tile_size), dtype=np.uint8)
            noise_pil = Image.fromarray(noise_pattern, 'L')
            full_img = Image.new('L', (w, h))
            for y in range(0, h, tile_size):
                for x in range(0, w, tile_size):
                    full_img.paste(noise_pil, (x, y))

            new_photo = ImageTk.PhotoImage(image=full_img)
            canvas.itemconfig(image_item, image=new_photo)
            canvas.image_ref = new_photo  # Crucial: prevent garbage collection

            # Schedule the next frame
            animation_id = self.root.after(100, self.animate_static_effect, monitor_id)
            self.preparation_overlays[monitor_id]['animation_id'] = animation_id
        except Exception as e:
            # This can happen if the window is destroyed during the process
            print(f"Error during static animation: {e}")

    # --- MODIFIED: _create_inactive_overlay (to include animation start) ---
    def _create_inactive_overlay(self, monitor):
        overlay = Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
        overlay.wm_attributes("-topmost", True)
        overlay.wm_attributes("-alpha", 0.7)

        canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        w, h = monitor['width'], monitor['height']

        image_item = canvas.create_image(0, 0, anchor="nw") # Create an empty image item first

        try:
            logo_image = Image.open("assets/logo.png").resize((120, 120), Image.Resampling.LANCZOS)
            logo_tk = ImageTk.PhotoImage(logo_image)
            canvas.create_image(w/2, h/2 - 50, image=logo_tk)
            canvas.logo_ref = logo_tk
        except Exception as e:
            print(f"Não foi possível carregar o logo para a sobreposição: {e}")

        canvas.create_text(w/2, h/2 + 40, text="Esta tela não será gravada.",
                            fill="white", font=("Segoe UI", 16, "bold"), justify="center")

        self.preparation_overlays[monitor['id']] = {
            'window': overlay,
            'canvas': canvas,
            'image_item': image_item,
            'animation_id': None
        }

        # Start the animation loop
        self.root.after(10, self.animate_static_effect, monitor['id'])

    # --- MODIFIED: _destroy_preparation_overlays ---
    def _destroy_preparation_overlays(self):
        if self.focus_check_id:
            self.root.after_cancel(self.focus_check_id)
            self.focus_check_id = None

        for monitor_id, overlay_info in list(self.preparation_overlays.items()):
            if overlay_info['animation_id']:
                self.root.after_cancel(overlay_info['animation_id'])
            overlay_info['window'].destroy()
        self.preparation_overlays.clear()

        self.recording_indicator.hide_preparation_mode()

    # --- MODIFIED: start_recording_mode ---
    def start_recording_mode(self, quality_profile="high", record_all_screens=False):
        if self.state == "preparing":
            self._destroy_preparation_overlays()
        elif self.state != "idle":
            return

        self.state = "recording"
        self.root.withdraw() # Garante que a janela principal esteja oculta
        time.sleep(0.2)

        target_monitor = self.active_monitor_for_recording if not record_all_screens else None
        self.thread_gravacao = threading.Thread(target=self.recording_thread, args=(target_monitor, quality_profile, record_all_screens), daemon=True)
        self.thread_gravacao.start()

        self.recording_indicator.show()
        self.start_time = time.time()
        self.update_chronometer_loop()

    # --- MODIFIED: stop_recording ---
    def stop_recording(self):
        if self.state == "recording":
            self.state = "idle"
            self.recording_indicator.hide()
            self.root.deiconify()
        elif self.state == "preparing":
            self.state = "idle"
            self._destroy_preparation_overlays()
            self.root.deiconify()

    def recording_thread(self, target_to_record, quality_profile, record_all_screens=False):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        quality_profile = config.get('Recording', 'quality', fallback='high')

        filename = os.path.join(self.save_path, f"Evidencia_Gravacao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4")

        try:
            cursor_img = Image.open("assets/cursor.png").convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
        except FileNotFoundError:
            cursor_img = None

        mouse_controller = MouseController()

        if record_all_screens:
            monitors = self.sct.monitors[1:]
            total_width = sum(m['width'] for m in monitors)
            max_height = max(m['height'] for m in monitors)

            if total_width % 2 != 0: total_width += 1
            if max_height % 2 != 0: max_height += 1

            width, height = total_width, max_height
            recording_fps = 15.0
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

        with mss.mss() as sct:
            while self.is_recording:
                loop_start_time = time.time()
                try:
                    if record_all_screens:
                        monitors_to_capture = sct.monitors[1:]
                        combined_frame = np.zeros((height, width, 3), dtype=np.uint8)
                        current_x_offset = 0

                        # Define a origem do Desktop Virtual para o cálculo do cursor
                        virtual_screen_left = sct.monitors[0]['left']
                        virtual_screen_top = sct.monitors[0]['top']

                        for monitor in monitors_to_capture:
                            sct_img = sct.grab(monitor)
                            frame_np = np.array(sct_img)
                            h_m, w_m, _ = frame_np.shape

                            # Converte de BGRA para BGR
                            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)
                            combined_frame[0:h_m, current_x_offset:current_x_offset + w_m] = frame_bgr
                            current_x_offset += w_m

                        final_frame_pil = Image.fromarray(cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB))

                        if cursor_img:
                            mouse_pos = mouse_controller.position
                            # Coordenadas do cursor relativas ao canto superior esquerdo do desktop virtual
                            cursor_x = mouse_pos[0] - virtual_screen_left
                            cursor_y = mouse_pos[1] - virtual_screen_top
                            final_frame_pil.paste(cursor_img, (cursor_x, cursor_y), cursor_img)

                        self.out.write(cv2.cvtColor(np.array(final_frame_pil), cv2.COLOR_RGB2BGR))

                    else:  # Lógica original para uma única tela
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
                    self.state = "idle" # Changed from is_recording = False to avoid race conditions

                sleep_time = (1/recording_fps) - (time.time() - loop_start_time)
                if sleep_time > 0: time.sleep(sleep_time)

        if self.out: self.out.release()

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
