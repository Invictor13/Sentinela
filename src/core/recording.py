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


class OverlaySelectionWindow(Toplevel):
    def __init__(self, parent, recorder_module):
        super().__init__(parent)
        self.recorder_module = recorder_module
        self.sct = mss.mss()

        # Configurações da janela de sobreposição
        self.configure(bg=COR_TRANSPARENTE)
        self.wm_attributes("-transparentcolor", COR_TRANSPARENTE)
        self.wm_attributes("-topmost", True)
        self.overrideredirect(True)

        # Obter a geometria de todo o desktop virtual
        total_width = sum(m["width"] for m in self.sct.monitors[1:])
        min_left = min(m["left"] for m in self.sct.monitors[1:])
        min_top = min(m["top"] for m in self.sct.monitors[1:])
        max_height = max(m["height"] for m in self.sct.monitors[1:])

        # A geometria para cobrir tudo pode ser complexa; vamos usar o monitor[0] por enquanto
        # que geralmente representa o desktop virtual inteiro.
        desktop = self.sct.monitors[0]
        self.geometry(f"{desktop['width']}x{desktop['height']}+{desktop['left']}+{desktop['top']}")

        # Canvas para escurecer a tela
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0)
        self.wm_attributes("-alpha", 0.5) # Opacidade da janela inteira
        self.canvas.pack(fill="both", expand=True)

        self.available_windows = []
        self.active_window = None
        self.highlight_rect = None

        self.desktop_offset_x = desktop['left']
        self.desktop_offset_y = desktop['top']

        self.refresh_window_list()
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_click)

        # Estado da seleção
        self.selection_locked = False
        self.selected_window = None
        self.quality_var = tk.StringVar(value="high")
        self.buttons = {}


    def refresh_window_list(self):
        self.available_windows = []
        seen_titles = set()
        # Nomes de janelas a serem ignoradas
        banned_titles = {"Program Manager", "Experiência de entrada do Windows", "Configurações", self.title()}

        all_windows = gw.getAllWindows()
        for window in all_windows:
            if (window.title and
                window.visible and
                not window.isMinimized and
                window.width > 100 and # Filtrar janelas muito pequenas
                window.height > 100 and
                window.title not in seen_titles and
                window.title not in banned_titles):
                self.available_windows.append(window)
                seen_titles.add(window.title)

    def on_mouse_move(self, event):
        # Coordenadas do mouse relativas à tela
        mouse_x, mouse_y = self.winfo_pointerxy()

        found_window = None
        for window in self.available_windows:
            if (window.left < mouse_x < window.right and
                window.top < mouse_y < window.bottom):
                found_window = window
                break

        if found_window and found_window != self.active_window:
            self.active_window = found_window
            if self.highlight_rect:
                self.canvas.delete(self.highlight_rect)

            # Ajustar coordenadas para o canvas
            x1 = window.left - self.desktop_offset_x
            y1 = window.top - self.desktop_offset_y
            x2 = window.right - self.desktop_offset_x
            y2 = window.bottom - self.desktop_offset_y

            self.highlight_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=COR_DESTAQUE, width=4, fill=COR_TRANSPARENTE
            )
        elif not found_window and self.active_window:
            self.active_window = None
            if self.highlight_rect:
                self.canvas.delete(self.highlight_rect)
                self.highlight_rect = None

    def on_mouse_click(self, event):
        if self.selection_locked:
            # A seleção está travada, verificar clique nos botões
            mouse_x, mouse_y = event.x, event.y
            for name, (x1, y1, x2, y2) in self.buttons.items():
                if x1 < mouse_x < x2 and y1 < mouse_y < y2:
                    if name == "record":
                        self.recorder_module.start_recording_mode(self.selected_window, self.quality_var.get())
                        self.destroy()
                    elif name == "cancel":
                        self.destroy()
                    break
        elif self.active_window:
            # Travar a seleção na janela ativa
            self.selection_locked = True
            self.selected_window = self.active_window
            self.canvas.unbind("<Motion>")
            self._draw_confirmation_controls()

    def _draw_confirmation_controls(self):
        # Coordenadas da janela selecionada, ajustadas para o canvas
        win_x1 = self.selected_window.left - self.desktop_offset_x
        win_y1 = self.selected_window.top - self.desktop_offset_y
        win_x2 = self.selected_window.right - self.desktop_offset_x
        win_y2 = self.selected_window.bottom - self.desktop_offset_y

        # Posição para os controles (abaixo da janela selecionada)
        controls_y = win_y2 + 10
        center_x = (win_x1 + win_x2) / 2

        # --- Botão Gravar (desenhado manualmente) ---
        btn_w, btn_h = 100, 30
        rec_x1 = center_x - btn_w - 5
        rec_y1 = controls_y
        rec_x2 = rec_x1 + btn_w
        rec_y2 = rec_y1 + btn_h
        self.canvas.create_rectangle(rec_x1, rec_y1, rec_x2, rec_y2, fill=COR_BOTAO, outline=COR_BOTAO, tags="controls")
        self.canvas.create_text(rec_x1 + btn_w/2, rec_y1 + btn_h/2, text="Gravar", fill="white", font=("Segoe UI", 10, "bold"), tags="controls")
        self.buttons["record"] = (rec_x1, rec_y1, rec_x2, rec_y2)

        # --- Botão Cancelar (desenhado manualmente) ---
        can_x1 = center_x + 5
        can_y1 = controls_y
        can_x2 = can_x1 + btn_w
        can_y2 = can_y1 + btn_h
        self.canvas.create_rectangle(can_x1, can_y1, can_x2, can_y2, fill="#a9a9a9", outline="#a9a9a9", tags="controls")
        self.canvas.create_text(can_x1 + btn_w/2, can_y1 + btn_h/2, text="Cancelar", fill="white", font=("Segoe UI", 10, "bold"), tags="controls")
        self.buttons["cancel"] = (can_x1, can_y1, can_x2, can_y2)

        # --- Opções de Qualidade (Radio Buttons) ---
        quality_frame = tk.Frame(self, bg="#333333")
        style = ttk.Style()
        style.configure("TFrame", background="#333333")
        style.configure("TRadiobutton", background="#333333", foreground="white", font=("Segoe UI", 9))

        rb_high = ttk.Radiobutton(quality_frame, text="Alta Qualidade", variable=self.quality_var, value="high", style="TRadiobutton")
        rb_compact = ttk.Radiobutton(quality_frame, text="Compacta", variable=self.quality_var, value="compact", style="TRadiobutton")
        rb_high.pack(side="left", padx=5)
        rb_compact.pack(side="left", padx=5)

        self.canvas.create_window(center_x, controls_y + btn_h + 20, window=quality_frame, tags="controls")

    def destroy(self):
        # Garantir que a janela principal reapareça
        if self.recorder_module:
            self.recorder_module.root.deiconify()
        super().destroy()


class ScreenRecordingModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.is_recording = False
        self.out = None
        self.start_time = None
        self.selection_window = None
        self.recording_indicator = RecordingIndicator(self.root, self)
        self.sct = mss.mss()
        self.thread_gravacao = None

    def open_recording_selection_ui(self):
        if self.is_recording or (self.selection_window and self.selection_window.winfo_exists()):
            return

        self.root.withdraw()
        self.selection_window = OverlaySelectionWindow(self.root, self)

    def start_recording_mode(self, target_to_record, quality_profile):
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
