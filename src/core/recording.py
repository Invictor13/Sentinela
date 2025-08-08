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

class ScreenRecordingModule:
    def __init__(self, root, save_path):
        self.root = root
        self.save_path = save_path
        self.is_recording = False
        self.out = None
        self.start_time = None
        self.selection_window = None
        self.selected_area = None
        self.selected_window_obj = None
        self.start_button = None
        self.preview_photo = None
        self.recording_indicator = RecordingIndicator(self.root, self)
        self.sct = mss.mss()
        self.thread_gravacao = None

    def open_recording_selection_ui(self):
        if self.is_recording or (self.selection_window and self.selection_window.winfo_exists()):
            return
        self.root.withdraw()
        self.selection_window = Toplevel(self.root)
        self.selection_window.title("Opção de Gravação")
        self.selection_window.configure(bg=COR_FUNDO_JANELA)
        self.selection_window.resizable(False, False)
        self.selection_window.wm_attributes("-topmost", True)

        main_frame = tk.Frame(self.selection_window, bg=COR_FUNDO_JANELA, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        left_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        right_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        right_frame.pack(side="left", fill="both", expand=True)

        tk.Label(left_frame, text="1. Selecione a Fonte", font=("Segoe UI", 12, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 10))
        self.monitor_var = tk.StringVar()
        monitor_options = ["Gravar Todos os Monitores"] + [f"Monitor {i}: {m['width']}x{m['height']}" for i, m in enumerate(self.sct.monitors[1:], 1)]
        self.monitor_combo = ttk.Combobox(left_frame, textvariable=self.monitor_var, values=monitor_options, state="readonly", width=35)
        self.monitor_combo.pack(fill='x', pady=5)
        self.monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_select)
        tk.Label(left_frame, text="Ou selecione uma janela:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).pack(pady=(10, 5), anchor='w')
        self.window_listbox = Listbox(left_frame, selectmode=SINGLE, bg=COR_CARD, fg=COR_TEXTO_SECUNDARIO, selectbackground=COR_BOTAO, font=("Segoe UI", 9), height=10)
        self.window_listbox.pack(expand=True, fill="both")
        self.window_listbox.bind("<<ListboxSelect>>", self.on_window_select)
        refresh_button = tk.Button(left_frame, text="Atualizar Lista", command=self.refresh_window_list, font=("Segoe UI", 9), relief=tk.FLAT)
        refresh_button.pack(pady=(5,0), fill='x')
        self.refresh_window_list()

        tk.Label(right_frame, text="2. Escolha a Qualidade", font=("Segoe UI", 12, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 10))

        self.quality_var = tk.StringVar(value="high")

        quality_options = {
            "high": ("Alta Qualidade (Textos Nítidos)", "Grava em até 1080p. Ideal para sistemas e documentos. Arquivos maiores."),
            "compact": ("Compacta (Web e E-mail)", "Grava em até 720p. Ideal para compartilhamento. Arquivos menores.")
        }

        for value, (text, desc) in quality_options.items():
            rb_frame = tk.Frame(right_frame, bg=COR_FUNDO_JANELA)
            rb_frame.pack(fill="x", pady=2)
            rb = ttk.Radiobutton(rb_frame, text=text, variable=self.quality_var, value=value)
            rb.pack(side="left", anchor="w")
            tk.Label(rb_frame, text=desc, font=("Segoe UI", 8), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).pack(side="left", anchor="w", padx=5)

        tk.Label(right_frame, text="3. Pré-visualização", font=("Segoe UI", 12, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(anchor="w", pady=(15, 5))
        preview_container = tk.Frame(right_frame, bg="black", width=480, height=270)
        preview_container.pack(); preview_container.pack_propagate(False)
        self.preview_label = tk.Label(preview_container, bg="black", text="Selecione uma fonte para ver a prévia", fg="white", font=("Segoe UI", 10))
        self.preview_label.pack(expand=True, fill="both")

        control_frame = tk.Frame(self.selection_window, bg=COR_FUNDO_JANELA, pady=10, padx=10)
        control_frame.pack(fill="x")
        self.start_button = tk.Button(control_frame, text="Iniciar Gravação", command=self.start_recording_from_preview, font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, state=tk.DISABLED)
        self.start_button.pack(side="right")
        cancel_button = tk.Button(control_frame, text="Cancelar", command=self.close_selection_window, font=("Segoe UI", 10), relief=tk.FLAT)
        cancel_button.pack(side="right", padx=10)

        self.selection_window.protocol("WM_DELETE_WINDOW", self.close_selection_window)
        self.selection_window.lift(); self.selection_window.focus_force()

    def refresh_window_list(self):
        self.window_listbox.delete(0, END)
        self.available_windows = []
        seen_titles = set()

        banned_titles = {"Program Manager", "Experiência de entrada do Windows", "Configurações", "Opção de Gravação"}

        all_windows = gw.getAllWindows()
        for window in all_windows:
            if (window.title and
                window.visible and
                not window.isMinimized and
                window.width > 10 and
                window.height > 10 and
                window.title not in seen_titles and
                window.title not in banned_titles):

                self.available_windows.append(window)
                self.window_listbox.insert(END, window.title)
                seen_titles.add(window.title)

    def on_monitor_select(self, event):
        self.window_listbox.selection_clear(0, END)
        selected_index = self.monitor_combo.current()
        self.selected_window_obj = None
        self.start_button.config(state=tk.DISABLED)
        if selected_index == 0:
            self.selected_area = self.sct.monitors[0]
        else:
            self.selected_area = self.sct.monitors[selected_index]
        self.update_static_preview()

    def on_window_select(self, event):
        try:
            self.monitor_var.set('')
            selected_index = self.window_listbox.curselection()[0]
            selected_title = self.window_listbox.get(selected_index)
            self.start_button.config(state=tk.DISABLED)

            target_window = next((w for w in self.available_windows if w.title == selected_title), None)
            if target_window:
                self.selected_window_obj = target_window
                self.selected_area = {"top": target_window.top, "left": target_window.left, "width": target_window.width, "height": target_window.height}
                self.update_static_preview()
        except IndexError:
            pass

    def update_static_preview(self):
        if not self.selection_window or not self.selection_window.winfo_exists() or not self.selected_area:
            return
        original_geometry, sct_img = None, None
        try:
            original_geometry = self.selection_window.geometry()
            self.selection_window.geometry("+3000+3000")
            self.root.update_idletasks()
            time.sleep(0.1)
            sct_img = self.sct.grab(self.selected_area)
        except Exception as e:
            print(f"Erro na pré-visualização: {e}")
        finally:
            if original_geometry and self.selection_window and self.selection_window.winfo_exists():
                self.selection_window.geometry(original_geometry)
        if sct_img:
            try:
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img_resized = img.resize((480, 270), Image.Resampling.LANCZOS)
                self.preview_photo = ImageTk.PhotoImage(image=img_resized)
                self.preview_label.config(image=self.preview_photo, text="")
                self.start_button.config(state=tk.NORMAL)
            except Exception as e:
                print(f"Erro ao processar pré-visualização: {e}")

    def start_recording_from_preview(self):
        if not self.selected_area:
            return
        target_to_record = self.selected_window_obj or self.selected_area
        quality_profile = self.quality_var.get()
        if self.selected_window_obj:
            try:
                self.selected_window_obj.activate()
                time.sleep(0.3)
            except Exception as e:
                print(f"Falha ao ativar janela: {e}")
        self.close_selection_window()
        self.start_recording_mode(target_to_record, quality_profile)

    def close_selection_window(self):
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.root.deiconify()

    def start_recording_mode(self, target_to_record, quality_profile):
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
