import tkinter as tk
from tkinter import font as tkfont, ttk
from tkinter import messagebox, Toplevel, Listbox, END, SINGLE, simpledialog, filedialog
import threading
import time
import os
import re
import subprocess
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np
import cv2
from pynput import keyboard
from pynput.mouse import Controller as MouseController
import pygetwindow as gw
import random
import mss
import mss.tools
import ctypes
import configparser
import sys
from pystray import MenuItem as item, Icon as icon, Menu
import shutil

# --- CORREÇÃO DE DPI SCALING ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except AttributeError:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"Alerta de DPI: Não foi possível configurar a sensibilidade de DPI. Erro: {e}")

# --- FUNÇÃO DE RECURSOS ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURAÇÕES GLOBAIS ---
CONFIG_FILE = "config.ini"
USER_DOCUMENTS_PATH = os.path.join(os.path.expanduser("~"), "Documents")
DEFAULT_SAVE_LOCATION_FALLBACK = os.path.join(USER_DOCUMENTS_PATH, "SentinelaEvidencias")

def load_app_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['Hotkeys'] = {'CaptureInfo': 'Shift + F9', 'RecordInfo': 'Shift + F10'}
        config['Paths'] = {'DefaultSaveLocation': DEFAULT_SAVE_LOCATION_FALLBACK}
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    config.read(CONFIG_FILE)
    if 'Paths' not in config: config['Paths'] = {'DefaultSaveLocation': DEFAULT_SAVE_LOCATION_FALLBACK}
    current_save_location = config.get('Paths', 'DefaultSaveLocation', fallback=DEFAULT_SAVE_LOCATION_FALLBACK)
    os.makedirs(current_save_location, exist_ok=True)
    return {"DefaultSaveLocation": current_save_location, "config_parser_obj": config}

def save_app_config(config_parser_obj, save_path_to_save):
    config_parser_obj['Paths']['DefaultSaveLocation'] = save_path_to_save
    with open(CONFIG_FILE, 'w') as configfile:
        config_parser_obj.write(configfile)

# --- ESTADO GLOBAL E CONSTANTES ---
app_config_data = load_app_config()
DEFAULT_SAVE_PATH = app_config_data["DefaultSaveLocation"]

COR_FUNDO_JANELA = "#f0f5f0"
COR_CARD = "#ffffff"
COR_TEXTO_PRINCIPAL = "#005a36"
COR_TEXTO_SECUNDARIO = "#555555"
COR_BOTAO = "#00995D"
COR_BOTAO_HOVER = "#007a4a"
COR_BOTAO_SECUNDARIO = "#7f8c8d"
COR_BOTAO_SECUNDARIO_HOVER = "#6c7a7d"
PALETA_BOLHAS = ["#00b37a", "#00a36e", "#00995d", "#008f5d", "#007a4a"]

capturando_tela = False
gravando_tela = False
screenshots = []
thread_gravacao = None

# --- MÓDULOS DE LÓGICA E UI AUXILIAR ---
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

def show_success_dialog(root, message, folder_path, specific_path_to_copy):
    dialog = Toplevel(root)
    dialog.title("Sucesso")
    dialog.configure(bg=COR_FUNDO_JANELA)
    dialog.resizable(False, False)
    dialog.wm_attributes("-topmost", True)
    root.update_idletasks()
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    dialog_width, dialog_height = 450, 220
    x = (screen_width // 2) - (dialog_width // 2)
    y = (screen_height // 2) - (dialog_height // 2)
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    tk.Label(dialog, text="Operação Concluída com Sucesso!", font=("Segoe UI", 12, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).pack(pady=(20, 10))
    tk.Label(dialog, text=f"A pasta de destino já foi aberta.\n{message}", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO, wraplength=430).pack()
    
    button_frame = tk.Frame(dialog, bg=COR_FUNDO_JANELA)
    button_frame.pack(pady=20, expand=True)

    def copy_path_action():
        dialog.clipboard_clear()
        dialog.clipboard_append(specific_path_to_copy)
        copy_button.config(text="Copiado!", state=tk.DISABLED)
        dialog.after(1500, lambda: copy_button.config(text="Copiar Caminho", state=tk.NORMAL))
    copy_button = tk.Button(button_frame, text="Copiar Caminho", command=copy_path_action, font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=10, pady=5)
    copy_button.pack(side="left", padx=5)

    close_button = tk.Button(button_frame, text="Concluir", command=dialog.destroy, font=("Segoe UI", 10), relief=tk.FLAT, padx=10, pady=5)
    close_button.pack(side="left", padx=5)
    close_button.focus_set()
    
    dialog.after(7000, dialog.destroy)

class Bubble:
    def __init__(self, canvas, width, height):
        self.canvas, self.width, self.height = canvas, width, height
        self.radius = random.randint(20, 50)
        self.x, self.y = random.randint(self.radius, width - self.radius), random.randint(self.radius, height - self.radius)
        self.dx, self.dy = random.choice([-1.5, -1, 1, 1.5]), random.choice([-1.5, -1, 1, 1.5])
        self.color = random.choice(PALETA_BOLHAS)
        self.id = self.canvas.create_oval(self.x-self.radius, self.y-self.radius, self.x+self.radius, self.y+self.radius, fill=self.color, outline="")
    def move(self):
        self.x += self.dx; self.y += self.dy
        if not self.radius < self.x < self.width - self.radius: self.dx *= -1
        if not self.radius < self.y < self.height - self.radius: self.dy *= -1
        self.canvas.coords(self.id, self.x-self.radius, self.y-self.radius, self.x+self.radius, self.y+self.radius)

class MainApplication(tk.Frame):
    def __init__(self, parent, capture_module, recording_module):
        super().__init__(parent)
        self.parent = parent
        self.capture_module = capture_module
        self.recording_module = recording_module
        self.configure(bg=COR_FUNDO_JANELA)
        
        self.canvas = tk.Canvas(self, bg=COR_FUNDO_JANELA, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bubbles = [Bubble(self.canvas, 1280, 720) for _ in range(20)]
        self.create_widgets()
        self.animate_bubbles()
        self.parent.bind("<Configure>", self.on_window_resize)

    def animate_bubbles(self):
        for bubble in self.bubbles:
            bubble.move()
        self.after(33, self.animate_bubbles)

    def create_widgets(self):
        self.main_card_frame = tk.Frame(self.canvas, bg=COR_CARD, bd=1, relief="solid")
        self.main_card_id = self.canvas.create_window(0, 0, window=self.main_card_frame, anchor="center")
        header_container = tk.Frame(self.main_card_frame, bg=COR_CARD, padx=20, pady=15)
        header_container.pack(fill="x", expand=True, pady=(10,0))
        try:
            logo_image = Image.open(resource_path("logo.png")); logo_image.thumbnail((200, 60)); self.logo_tk = ImageTk.PhotoImage(logo_image)
            tk.Label(header_container, image=self.logo_tk, bg=COR_CARD).pack(pady=(0,10))
        except FileNotFoundError: pass
        tk.Label(header_container, text="Sentinela Unimed", font=("Segoe UI", 26, "bold"), bg=COR_CARD, fg=COR_TEXTO_PRINCIPAL).pack()
        tk.Label(header_container, text="Gravador de evidências simples e seguro", font=("Segoe UI", 10), bg=COR_CARD, fg=COR_TEXTO_SECUNDARIO).pack(pady=(0,10))
        tk.Frame(self.main_card_frame, height=1, bg="#e0e0e0").pack(fill="x", padx=40, pady=(15,10))
        content_container = tk.Frame(self.main_card_frame, bg=COR_CARD, padx=40, pady=20)
        content_container.pack(expand=True, fill="both")
        btn1 = tk.Button(content_container, text="INICIAR CAPTURA (Shift+F9)", font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=20, pady=8, command=self.capture_module.start_capture_mode)
        btn1.pack(pady=(5,10), fill='x')
        btn2 = tk.Button(content_container, text="INICIAR GRAVAÇÃO (Shift+F10)", font=("Segoe UI", 10, "bold"), bg=COR_BOTAO, fg="white", relief=tk.FLAT, padx=20, pady=8, command=self.recording_module.open_recording_selection_ui)
        btn2.pack(pady=(5,10), fill='x')
        for btn in [btn1, btn2]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_HOVER))
            btn.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO))
        
        footer_frame = tk.Frame(self.main_card_frame, bg="#f5f5f5", pady=5)
        footer_frame.pack(side="bottom", fill="x", pady=(10,0))
        
        btn_open_folder = tk.Button(footer_frame, text="Abrir Pasta de Evidências", font=("Segoe UI", 8, "bold"), command=lambda: open_evidence_folder(), relief=tk.FLAT, bg=COR_BOTAO_SECUNDARIO, fg="white")
        btn_open_folder.pack(side=tk.LEFT, padx=10)
        btn_open_folder.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_SECUNDARIO_HOVER))
        btn_open_folder.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO_SECUNDARIO))
        
        tk.Label(footer_frame, text="Código by Victor Ladislau Viana", font=("Segoe UI", 8), bg=footer_frame.cget('bg'), fg=COR_TEXTO_SECUNDARIO).pack(side=tk.LEFT, padx=10)
        
        btn_settings = tk.Button(footer_frame, text="⚙", font=("Segoe UI", 12), command=lambda: open_settings(self.parent), relief=tk.FLAT, bg=footer_frame.cget('bg'), fg=COR_TEXTO_SECUNDARIO)
        btn_settings.pack(side=tk.RIGHT, padx=10)
        
        self.parent.after(10, self.on_window_resize)

    def on_window_resize(self, event=None):
        w, h = self.parent.winfo_width(), self.parent.winfo_height()
        self.canvas.config(width=w, height=h)
        if hasattr(self, 'main_card_id'): self.canvas.coords(self.main_card_id, w/2, h/2)
        for bubble in self.bubbles: bubble.width, bubble.height = w,h

class CaptureIndicator(Toplevel):
    def __init__(self, parent, capture_module):
        super().__init__(parent)
        self.capture_module = capture_module
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg='#2b2b2b')
        container = tk.Frame(self, bg=self.cget('bg'))
        container.pack(padx=10, pady=5)
        self.count_label = tk.Label(container, text="Capturas: 0", font=("Segoe UI", 12, "bold"), fg="white", bg=self.cget('bg'))
        self.count_label.pack(side="left", padx=(0,15))
        info_label = tk.Label(container, text="Pressione Shift+F9 para capturar", font=("Segoe UI", 10), fg="#cccccc", bg=self.cget('bg'))
        info_label.pack(side="left", padx=(0,15))
        stop_button = tk.Button(container, text="CONCLUIR", font=("Segoe UI", 9, "bold"), fg="white", bg=COR_BOTAO, relief="flat", command=self.capture_module.stop_capture_mode, bd=0, padx=10, pady=2)
        stop_button.pack(side="left")
        stop_button.bind("<Enter>", lambda e: e.widget.config(bg=COR_BOTAO_HOVER))
        stop_button.bind("<Leave>", lambda e: e.widget.config(bg=COR_BOTAO))
        self.withdraw()

    def show(self):
        self.update_idletasks()
        parent_width = self.master.winfo_screenwidth()
        width = self.winfo_reqwidth()
        x, y = parent_width - width - 20, 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self): self.withdraw()
    def update_count(self, count): self.count_label.config(text=f"Capturas: {count}")

class ScreenCaptureModule:
    def __init__(self, root):
        self.root = root
        self.capture_indicator = CaptureIndicator(self.root, self)

    def start_capture_mode(self):
        global capturando_tela, screenshots
        if capturando_tela or gravando_tela: return
        capturando_tela = True
        screenshots = []
        self.capture_indicator.update_count(0)
        self.capture_indicator.show()
        self.root.withdraw()

    def take_screenshot(self):
        if capturando_tela:
            try:
                trigger_flash_animation(self.root)
                with mss.mss() as sct:
                    sct_img = sct.grab(sct.monitors[0])
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    screenshots.append(img)
                self.capture_indicator.update_count(len(screenshots))
            except Exception as e: print(f"Erro de Captura: {e}")

    def stop_capture_mode(self):
        global capturando_tela
        if not capturando_tela: return
        capturando_tela = False
        self.capture_indicator.hide()
        if screenshots:
            folder_name_input = simpledialog.askstring("Salvar Evidências", "Digite o nome da pasta para as capturas:", parent=self.root)
            base_folder_name = folder_name_input if folder_name_input and is_valid_foldername(folder_name_input) else f"Evidencias_Captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            target_save_path = os.path.join(DEFAULT_SAVE_PATH, base_folder_name)
            os.makedirs(target_save_path, exist_ok=True)
            for i, img in enumerate(screenshots): img.save(os.path.join(target_save_path, f"evidencia_{i+1}.png"))
            try:
                open_evidence_folder(target_save_path)
            except Exception as e: print(f"Não foi possível abrir a pasta: {e}")
            success_message = f"{len(screenshots)} capturas salvas."
            show_success_dialog(self.root, success_message, target_save_path, os.path.abspath(target_save_path))
        screenshots.clear()

class ScreenRecordingModule:
    def __init__(self, root):
        self.root = root
        self.is_recording, self.out, self.start_time, self.selection_window, self.selected_area, self.selected_window_obj, self.start_button, self.preview_photo = False, None, None, None, None, None, None, None
        self.recording_indicator = RecordingIndicator(self.root, self)
        self.sct = mss.mss()

    def open_recording_selection_ui(self):
        if capturando_tela or gravando_tela or (self.selection_window and self.selection_window.winfo_exists()): return
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
        # Codium: O Feitiço da Visão Pura.
        # Este novo encantamento de filtragem bane janelas fantasmas e duplicadas.
        self.window_listbox.delete(0, END)
        self.available_windows = []
        seen_titles = set()
        
        # Codium: Lista de títulos a serem banidos da seleção.
        banned_titles = {"Program Manager", "Experiência de entrada do Windows", "Configurações", "Opção de Gravação"}

        all_windows = gw.getAllWindows()
        for window in all_windows:
            # Filtros para garantir que a janela é "real" e relevante
            if (window.title and 
                not window.title.startswith("IDLE Shell") and
                window.visible and 
                not window.isMinimized and
                window.width > 10 and # Filtra janelas "fantasmas" sem dimensões reais
                window.height > 10 and
                window.title not in seen_titles and
                window.title not in banned_titles):
                
                self.available_windows.append(window)
                self.window_listbox.insert(END, window.title)
                seen_titles.add(window.title)

    def on_monitor_select(self, event):
        self.window_listbox.selection_clear(0, END)
        selected_index = self.monitor_combo.current()
        self.selected_window_obj = None; self.start_button.config(state=tk.DISABLED)
        if selected_index == 0: self.selected_area = self.sct.monitors[0]
        else: self.selected_area = self.sct.monitors[selected_index]
        self.update_static_preview()

    def on_window_select(self, event):
        try:
            self.monitor_var.set(''); selected_index = self.window_listbox.curselection()[0]
            selected_title = self.window_listbox.get(selected_index)
            self.start_button.config(state=tk.DISABLED)
            target_window = next((w for w in self.available_windows if w.title == selected_title), None)
            if target_window:
                self.selected_window_obj = target_window
                self.selected_area = {"top": target_window.top, "left": target_window.left, "width": target_window.width, "height": target_window.height}
                self.update_static_preview()
        except IndexError: pass

    def update_static_preview(self):
        if not self.selection_window or not self.selection_window.winfo_exists() or not self.selected_area: return
        original_geometry, sct_img = None, None
        try:
            original_geometry = self.selection_window.geometry()
            self.selection_window.geometry("+3000+3000")
            self.root.update_idletasks(); time.sleep(0.1)
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
                self.preview_label.config(image=self.preview_photo, text=""); self.start_button.config(state=tk.NORMAL)
            except Exception as e: print(f"Erro ao processar pré-visualização: {e}")

    def start_recording_from_preview(self):
        if not self.selected_area: return
        target_to_record = self.selected_window_obj or self.selected_area
        quality_profile = self.quality_var.get()
        if self.selected_window_obj:
            try: self.selected_window_obj.activate(); time.sleep(0.3)
            except Exception: pass
        self.close_selection_window()
        self.start_recording_mode(target_to_record, quality_profile)
    
    def close_selection_window(self):
        if self.selection_window: self.selection_window.destroy(); self.selection_window = None

    def start_recording_mode(self, target_to_record, quality_profile):
        global gravando_tela, thread_gravacao
        if gravando_tela: return
        gravando_tela, self.is_recording = True, True
        thread_gravacao = threading.Thread(target=self.recording_thread, args=(target_to_record, quality_profile), daemon=True)
        thread_gravacao.start()
        self.recording_indicator.update_time(0); self.start_time = time.time()
        self.recording_indicator.show(); self.update_chronometer_loop()

    def stop_recording(self):
        global gravando_tela
        if not gravando_tela: return
        self.is_recording = False; gravando_tela = False
        self.recording_indicator.hide()
    
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
            if output_width % 2 != 0: output_width -=1
            if output_height % 2 != 0: output_height -=1
            print(f"Alerta: Resolução original ({original_width}x{original_height}) redimensionada para ({output_width}x{output_height}) para otimização.")

        width, height = output_width, output_height
        
        filename = os.path.join(DEFAULT_SAVE_PATH, f"Evidencia_Gravacao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4")
        
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
        
        try: cursor_img = Image.open(resource_path("cursor.png")).convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
        except FileNotFoundError: cursor_img = None
        mouse_controller = MouseController()
        with mss.mss() as sct:
            while self.is_recording:
                loop_start_time = time.time()
                try:
                    if is_window_recording:
                        if not target_to_record.visible or target_to_record.isMinimized: self.is_recording = False; continue
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

class RecordingIndicator(Toplevel):
    def __init__(self, parent, recording_module):
        super().__init__(parent)
        self.recording_module = recording_module
        self.animation_id = None
        self.logo_photo = None
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg='#2b2b2b')
        container = tk.Frame(self, bg=self.cget('bg'))
        container.pack(padx=10, pady=5)
        
        # Codium: O Totem da Gravação.
        # Carrega o logo da Unimed e o exibe ao lado do texto "REC".
        try:
            logo_image = Image.open(resource_path("logo.png")).resize((20, 20), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(container, image=self.logo_photo, bg=self.cget('bg'))
            logo_label.pack(side="left", padx=(0, 5))
        except Exception as e:
            print(f"Alerta: Não foi possível carregar o ícone para o indicador de gravação. {e}")

        self.rec_label = tk.Label(container, text="REC", font=("Segoe UI", 12, "bold"), fg="#ff0000", bg=self.cget('bg'))
        self.rec_label.pack(side="left", padx=(0,10))
        
        self.time_label = tk.Label(container, text="00:00:00", font=("Segoe UI", 12, "bold"), fg="white", bg=self.cget('bg'))
        self.time_label.pack(side="left", padx=(0,10))
        self.info_label = tk.Label(container, text="Shift+F10 para parar", font=("Segoe UI", 10), fg="white", bg=self.cget('bg'))
        self.info_label.pack(side="left", padx=(0,15))
        self.stop_button = tk.Button(container, text="PARAR", font=("Segoe UI", 9, "bold"), fg="white", bg="#c70000", relief="flat", command=self.recording_module.stop_recording, bd=0, padx=10, pady=2)
        self.stop_button.pack(side="left", padx=(0, 5))
        self.withdraw()

    def _animate_rec(self):
        if not self.winfo_exists() or not self.recording_module.is_recording: return
        current_color = self.rec_label.cget("fg")
        new_color = self.cget('bg') if current_color == '#ff0000' else '#ff0000'
        self.rec_label.config(fg=new_color)
        self.animation_id = self.after(700, self._animate_rec)

    def show(self):
        self.update_idletasks()
        x, y = self.master.winfo_screenwidth() - self.winfo_reqwidth() - 20, 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        if self.animation_id is None: self._animate_rec()

    def hide(self):
        if self.animation_id: self.after_cancel(self.animation_id)
        self.animation_id = None
        self.withdraw()

    def update_time(self, elapsed_seconds):
        secs = int(elapsed_seconds)
        mins, secs = divmod(secs, 60)
        hrs, mins = divmod(mins, 60)
        self.time_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")

class SettingsWindow(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configurações"); self.geometry("500x180"); self.configure(bg=COR_FUNDO_JANELA)
        self.resizable(False, False); self.transient(parent); self.grab_set(); self.wm_attributes("-topmost", True)
        main_frame = tk.Frame(self, bg=COR_FUNDO_JANELA, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")
        tk.Label(main_frame, text="Atalhos (fixos para estabilidade):", font=("Segoe UI", 10, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))
        tk.Label(main_frame, text="Captura de Tela:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=1, column=0, sticky="w", pady=(0,5))
        tk.Label(main_frame, text="Shift + F9", font=("Segoe UI", 10, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=1, column=1, sticky="w", padx=5)
        tk.Label(main_frame, text="Gravação de Vídeo:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_SECUNDARIO).grid(row=2, column=0, sticky="w", pady=(0,5))
        tk.Label(main_frame, text="Shift + F10", font=("Segoe UI", 10, "bold"), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=2, column=1, sticky="w", padx=5)
        tk.Label(main_frame, text="Pasta Padrão:", font=("Segoe UI", 10), bg=COR_FUNDO_JANELA, fg=COR_TEXTO_PRINCIPAL).grid(row=3, column=0, sticky="w", pady=(10,0))
        self.save_path_var = tk.StringVar(value=DEFAULT_SAVE_PATH)
        tk.Entry(main_frame, textvariable=self.save_path_var, state="readonly").grid(row=3, column=1, sticky="ew", padx=5)
        browse_button = tk.Button(main_frame, text="Procurar...", command=self.browse_save_path, font=("Segoe UI", 9))
        browse_button.grid(row=3, column=2, padx=(5,0))
        buttons_frame = tk.Frame(main_frame, bg=COR_FUNDO_JANELA)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=(20,0))
        tk.Button(buttons_frame, text="Salvar Pasta", command=self.save_settings, font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        tk.Button(buttons_frame, text="Fechar", command=self.destroy, font=("Segoe UI", 10)).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def browse_save_path(self):
        new_path = filedialog.askdirectory(initialdir=self.save_path_var.get(), parent=self)
        if new_path: self.save_path_var.set(new_path)

    def save_settings(self):
        global DEFAULT_SAVE_PATH
        new_save_path = self.save_path_var.get()
        try:
            os.makedirs(new_save_path, exist_ok=True)
            with open(os.path.join(new_save_path, ".test"), "w") as f: f.write("test")
            os.remove(os.path.join(new_save_path, ".test"))
        except: messagebox.showerror("Erro de Caminho", "Não é possível escrever no caminho.", parent=self); return
        save_app_config(app_config_data["config_parser_obj"], new_save_path)
        DEFAULT_SAVE_PATH = new_save_path
        app_config_data["DefaultSaveLocation"] = new_save_path
        messagebox.showinfo("Sucesso", "Configurações de pasta salvas.", parent=self)
        self.destroy()

# --- LÓGICA DE CONTROLE E THREADS ---
def key_listener_thread_proc(capture_module, recording_module, root_window):
    current_keys = set()
    CAPTURE_COMBO, RECORD_COMBO = {keyboard.Key.shift, keyboard.Key.f9}, {keyboard.Key.shift, keyboard.Key.f10}
    def on_press(key):
        if key in {keyboard.Key.shift, keyboard.Key.f9, keyboard.Key.f10}: current_keys.add(key)
        if CAPTURE_COMBO.issubset(current_keys):
            if capturando_tela: root_window.after(0, capture_module.take_screenshot)
            elif not gravando_tela: root_window.after(0, capture_module.start_capture_mode)
        elif RECORD_COMBO.issubset(current_keys):
            if gravando_tela: root_window.after(0, recording_module.stop_recording)
            elif not capturando_tela: root_window.after(0, recording_module.open_recording_selection_ui)
    def on_release(key):
        try: current_keys.remove(key)
        except KeyError: pass
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener: listener.join()

def open_settings(root): SettingsWindow(root)
def setup_tray_icon(icon_instance): icon_instance.run()
def quit_application(icon, root): 
    icon.stop()
    root.quit()
    sys.exit()

def show_main_window(root): root.deiconify(); root.lift(); root.focus_force()
def open_evidence_folder(path=None):
    folder_to_open = path or DEFAULT_SAVE_PATH
    try: subprocess.Popen(f'explorer "{os.path.realpath(folder_to_open)}"')
    except Exception as e: print(f"Não foi possível abrir a pasta de evidências: {e}")

# --- BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sentinela Unimed")
    root.protocol("WM_DELETE_WINDOW", root.withdraw)
    root.geometry("1280x720")
    try:
        icon_path_ico = resource_path('logo.ico')
        root.iconbitmap(icon_path_ico)
    except (tk.TclError, FileNotFoundError): icon_path_ico = None
    capture_module, recording_module = ScreenCaptureModule(root), ScreenRecordingModule(root)
    main_app = MainApplication(root, capture_module, recording_module)
    main_app.pack(side="top", fill="both", expand=True)
    root.withdraw()
    listener_thread = threading.Thread(target=key_listener_thread_proc, args=(capture_module, recording_module, root), daemon=True)
    listener_thread.start()
    try:
        image = Image.open(icon_path_ico if icon_path_ico else resource_path("logo.png"))
    except FileNotFoundError: image = Image.new('RGB', (64, 64), color = '#00995D')
    menu = (
        item('Exibir Sentinela', lambda: show_main_window(root), default=True), Menu.SEPARATOR,
        item('Capturar Tela (Shift+F9)', lambda: root.after(0, capture_module.start_capture_mode)),
        item('Gravar Vídeo (Shift+F10)', lambda: root.after(0, recording_module.open_recording_selection_ui)),
        item('Abrir Pasta de Evidências', lambda: open_evidence_folder()), Menu.SEPARATOR,
        item('Configurações', lambda: root.after(0, open_settings, root)),
        item('Sair', lambda: quit_application(tray_icon, root))
    )
    tray_icon = icon("Sentinela", image, "Sentinela Unimed", menu)
    tray_thread = threading.Thread(target=setup_tray_icon, args=(tray_icon,), daemon=True)
    tray_thread.start()
    root.mainloop()
