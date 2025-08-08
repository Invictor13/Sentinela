import os
import time
import threading
from datetime import datetime
import cv2
import mss
import numpy as np
from PIL import Image, ImageTk
from pynput.mouse import Controller as MouseController
import pygetwindow as gw
import tkinter as tk
from tkinter import Toplevel, Listbox, END, SINGLE, ttk, messagebox

from ..ui.recording_indicator import RecordingIndicator
from ..ui.dialogs import show_success_dialog

COR_FUNDO_JANELA = "#f0f5f0"
COR_CARD = "#ffffff"
COR_TEXTO_PRINCIPAL = "#005a36"
COR_TEXTO_SECUNDARIO = "#555555"
COR_BOTAO = "#00995D"
COR_DESTAQUE = "#00b37a"
COR_TRANSPARENTE = "white"


class ShadowCloakManager:
    def __init__(self, recorder_module):
        self.recorder_module = recorder_module
        self.sct = mss.mss()
        self.mouse_controller = MouseController()
        self.overlays = []
        self.active_overlay = None
        self.highlighted_window = None
        self.available_windows = []

        self._create_overlays()
        self.refresh_window_list()

    def _create_overlays(self):
        mouse_pos = self.mouse_controller.position
        active_monitor = None
        # O monitor[0] em MSS é o desktop virtual completo, os seguintes são os monitores individuais.
        monitors = self.sct.monitors[1:]

        for m in monitors:
            if m['left'] <= mouse_pos[0] < m['left'] + m['width'] and \
               m['top'] <= mouse_pos[1] < m['top'] + m['height']:
                active_monitor = m
                break

        if not active_monitor and monitors:
            active_monitor = monitors[0]

        for monitor in monitors:
            is_active = (monitor == active_monitor)
            overlay = Toplevel(self.recorder_module.root)
            overlay.overrideredirect(True)
            overlay.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
            overlay.wm_attributes("-topmost", True)

            if is_active:
                self.active_overlay = overlay
                self._setup_active_overlay(overlay, monitor)
            else:
                self._setup_inactive_overlay(overlay, monitor)

            self.overlays.append(overlay)

    def _setup_inactive_overlay(self, overlay, monitor):
        overlay.wm_attributes("-alpha", 0.6)
        canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        w, h = monitor['width'], monitor['height']

        try:
            # Efeito de ruído estático
            tile_size = 128
            noise = np.random.randint(0, 35, (tile_size, tile_size), dtype=np.uint8)
            noise_pil = Image.fromarray(noise, 'L')
            full_img = Image.new('L', (w, h))
            for y_pos in range(0, h, tile_size):
                for x_pos in range(0, w, tile_size):
                    full_img.paste(noise_pil, (x_pos, y_pos))

            noise_tk = ImageTk.PhotoImage(full_img)
            canvas.create_image(0, 0, image=noise_tk, anchor="nw")
            overlay.noise_ref = noise_tk
        except Exception as e:
            print(f"Falha ao criar efeito de ruído: {e}")

        try:
            logo_image = Image.open("assets/logo.png")
            logo_image.thumbnail((150, 150), Image.Resampling.LANCZOS)
            logo_tk = ImageTk.PhotoImage(logo_image)
            canvas.create_image(w/2, h/2 - 60, image=logo_tk)
            overlay.logo_ref = logo_tk
        except Exception as e:
            print(f"Não foi possível carregar o logo para a sobreposição: {e}")

        canvas.create_text(w/2, h/2 + 50, text="ESTA TELA NÃO ESTÁ SENDO GRAVADA",
                            fill="white", font=("Segoe UI", 18, "bold"), justify="center")
        canvas.create_text(w/2, h/2 + 85, text="A gravação ocorrerá na tela ativa.",
                            fill="white", font=("Segoe UI", 14), justify="center")

    def _setup_active_overlay(self, overlay, monitor):
        overlay.wm_attributes("-alpha", 0.5)
        overlay.wm_attributes("-transparentcolor", "white")
        overlay.config(bg='white') # Fundo branco que será transparente

        self.active_canvas = tk.Canvas(overlay, bg="white", highlightthickness=0)
        self.active_canvas.pack(fill="both", expand=True)
        self.active_canvas.create_rectangle(0, 0, monitor['width'], monitor['height'], fill="black", outline="")

        overlay.bind("<Motion>", self.on_mouse_move)

        self.monitor_offset = {'x': monitor['left'], 'y': monitor['top']}
        self.highlight_rect = None
        self.seal_elements = []

    def refresh_window_list(self):
        self.available_windows = []
        banned_titles = {"Program Manager", "Windows Input Experience", "Configurações"}
        for o in self.overlays:
            banned_titles.add(o.title())

        for window in gw.getAllWindows():
            if (window.title and window.visible and not window.isMinimized and
                window.width > 150 and window.height > 150 and window.title not in banned_titles):
                self.available_windows.append(window)

    def on_mouse_move(self, event):
        mouse_x, mouse_y = self.mouse_controller.position

        found_window = None
        for window in self.available_windows:
            if window.left < mouse_x < window.right and window.top < mouse_y < window.bottom:
                found_window = window
                break

        if self.highlighted_window != found_window:
            self.highlighted_window = found_window
            self._update_highlight()

    def _update_highlight(self):
        # Limpar destaques e selos antigos do canvas
        if self.highlight_rect:
            self.active_canvas.delete(self.highlight_rect)
            self.highlight_rect = None
        for item in self.seal_elements:
            self.active_canvas.delete(item)
        self.seal_elements = []

        if self.highlighted_window:
            win = self.highlighted_window
            # Coordenadas relativas ao monitor ativo
            x1 = win.left - self.monitor_offset['x']
            y1 = win.top - self.monitor_offset['y']
            x2 = win.right - self.monitor_offset['x']
            y2 = win.bottom - self.monitor_offset['y']

            self.highlight_rect = self.active_canvas.create_rectangle(
                x1, y1, x2, y2, outline="#00e676", width=5, fill="")

            self._draw_pre_confirmation_seal(x1, y1)

    def _draw_pre_confirmation_seal(self, x, y):
        seal_w, seal_h = 280, 55
        seal_x, seal_y = x + 10, y + 10

        rect = self.active_canvas.create_rectangle(
            seal_x, seal_y, seal_x + seal_w, seal_y + seal_h,
            fill="black", outline="#333333", width=1)

        rec_text = self.active_canvas.create_text(
            seal_x + 30, seal_y + seal_h / 2,
            text="REC", fill="red", font=("Segoe UI", 14, "bold"))

        msg_text = self.active_canvas.create_text(
            seal_x + 60, seal_y + seal_h / 2,
            text="Alvo na mira. Pressione Ctrl+F10\npara INICIAR a gravação.",
            fill="white", font=("Segoe UI", 9), anchor="w")

        self.seal_elements.extend([rect, rec_text, msg_text])

    def get_highlighted_window(self):
        return self.highlighted_window

    def destroy(self):
        for overlay in self.overlays:
            overlay.destroy()
        self.overlays = []


class ScreenRecordingModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.is_recording = False
        self.selection_in_progress = False
        self.out = None
        self.start_time = None
        self.selection_manager = None
        self.recording_indicator = RecordingIndicator(self.root, self)
        self.sct = mss.mss()
        self.thread_gravacao = None

    def open_recording_selection_ui(self):
        if self.is_recording or self.selection_in_progress:
            return

        self.selection_in_progress = True
        self.root.withdraw()
        self.selection_manager = ShadowCloakManager(self)

    def confirm_recording_selection(self):
        if not self.selection_in_progress or not self.selection_manager:
            return

        target_window = self.selection_manager.get_highlighted_window()

        if target_window:
            self.selection_manager.destroy()
            self.selection_manager = None
            # O padrão de qualidade será 'high' por enquanto, conforme o novo fluxo não pede input.
            self.start_recording_mode(target_window, "high")
        else:
            # Opcional: Adicionar um feedback sonoro ou visual de que nenhuma janela foi selecionada.
            print("Tentativa de confirmação de gravação sem uma janela em foco.")


    def start_recording_mode(self, target_to_record, quality_profile):
        self.selection_in_progress = False
        # Adicionar uma pequena pausa para a janela de overlay fechar
        time.sleep(0.2)

        # Ativar a janela alvo para garantir que ela esteja em primeiro plano
        if hasattr(target_to_record, 'title'):
            try:
                target_to_record.activate()
                time.sleep(0.3) # Pausa para a ativação da janela
            except Exception as e:
                print(f"Falha ao ativar a janela selecionada: {e}")

        if self.is_recording:
            return
        self.is_recording = True
        self.thread_gravacao = threading.Thread(target=self.recording_thread, args=(target_to_record, quality_profile), daemon=True)
        self.thread_gravacao.start()
        self.recording_indicator.update_time(0)
        self.start_time = time.time()
        self.recording_indicator.show()
        self.update_chronometer_loop()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.recording_indicator.hide()
        self.root.deiconify()

    def recording_thread(self, target_to_record, quality_profile):
        is_window_recording = hasattr(target_to_record, 'title')

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
