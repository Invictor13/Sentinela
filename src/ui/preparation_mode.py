import tkinter as tk
from tkinter import Toplevel
import mss
import numpy as np
from PIL import Image, ImageTk
from pynput.mouse import Controller as MouseController
from src.utils import resource_path

class PreparationOverlayManager:
    """
    Manages the visual preparation mode for screen capture and recording.
    This includes creating overlays on inactive screens, managing focus
    switching between monitors, and showing a readiness indicator on the
    active screen.
    """
    def __init__(self, root, indicator, indicator_text, inactive_text="This screen will not be used.", logo_path=None):
        self.root = root
        self.indicator = indicator
        self.indicator_text = indicator_text
        self.inactive_text = inactive_text
        self.logo_path = logo_path if logo_path is not None else resource_path("logo.png")

        self.sct = mss.mss()
        self.overlays = {}
        self.active_monitor = None
        self.focus_check_id = None
        self.is_running = False

    def get_active_monitor(self):
        """Returns the dictionary of the currently active monitor."""
        return self.active_monitor

    def start(self):
        """Starts the preparation mode."""
        if self.is_running:
            return
        self.is_running = True
        self.root.withdraw()

        mouse_pos = MouseController().position
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

        self.active_monitor = initial_active_monitor

        # Create overlays for all monitors
        for monitor in monitors:
            if self.active_monitor and monitor['id'] == self.active_monitor['id']:
                # Active monitor gets the preparation indicator
                self.indicator.show_preparation_mode(monitor, self.indicator_text)
            else:
                # Inactive monitors get the dark, noisy overlay
                self._create_inactive_overlay(monitor)

        # Start tracking mouse movement
        self.focus_check_id = self.root.after(250, self._update_active_screen_focus)

    def destroy(self):
        """Destroys all preparation UI elements and stops loops."""
        if not self.is_running:
            return
        self.is_running = False

        if self.focus_check_id:
            self.root.after_cancel(self.focus_check_id)
            self.focus_check_id = None

        for monitor_id, overlay_info in list(self.overlays.items()):
            if overlay_info.get('animation_id'):
                self.root.after_cancel(overlay_info['animation_id'])
            overlay_info['window'].destroy()
        self.overlays.clear()

        self.indicator.hide_preparation_mode()
        # We don't deiconify the root window here, the calling module should do that.

    def _update_active_screen_focus(self):
        if not self.is_running:
            return

        mouse_pos = MouseController().position
        monitors = [{**m, 'id': i} for i, m in enumerate(self.sct.monitors[1:])]

        new_active_monitor = None
        for m in monitors:
            if m['left'] <= mouse_pos[0] < m['left'] + m['width'] and \
               m['top'] <= mouse_pos[1] < m['top'] + m['height']:
                new_active_monitor = m
                break

        if new_active_monitor and self.active_monitor and new_active_monitor['id'] != self.active_monitor['id']:
            self._swap_focus(new_active_monitor)

        self.focus_check_id = self.root.after(250, self._update_active_screen_focus)

    def _swap_focus(self, new_monitor):
        old_monitor = self.active_monitor

        # Deactivate the old monitor: hide indicator and create inactive overlay
        self.indicator.hide_preparation_mode()
        if old_monitor:
            self._create_inactive_overlay(old_monitor)

        # Activate the new monitor: destroy inactive overlay and show indicator
        if new_monitor['id'] in self.overlays:
            overlay_info = self.overlays.pop(new_monitor['id'])
            if overlay_info.get('animation_id'):
                self.root.after_cancel(overlay_info['animation_id'])
            overlay_info['window'].destroy()

        self.active_monitor = new_monitor
        self.indicator.show_preparation_mode(new_monitor, self.indicator_text)


    def _create_inactive_overlay(self, monitor):
        overlay = Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
        overlay.wm_attributes("-topmost", True)
        overlay.wm_attributes("-alpha", 0.7)

        canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        w, h = monitor['width'], monitor['height']
        image_item = canvas.create_image(0, 0, anchor="nw")

        try:
            # --- Enhanced Logo Resizing ---
            logo_original = Image.open(self.logo_path)
            original_width, original_height = logo_original.size

            # Calculate new height to be 20% of the monitor's height
            target_height = int(h * 0.20)

            # Maintain aspect ratio
            aspect_ratio = original_width / original_height
            target_width = int(target_height * aspect_ratio)

            # Resize with high-quality downsampling
            logo_resized = logo_original.resize((target_width, target_height), Image.Resampling.LANCZOS)

            logo_tk = ImageTk.PhotoImage(logo_resized)
            canvas.create_image(w/2, h/2 - (target_height / 2), image=logo_tk) # Adjust vertical position based on new size
            canvas.logo_ref = logo_tk
        except Exception as e:
            print(f"Could not load logo for overlay: {e}")

        canvas.create_text(w/2, h/2 + 40, text=self.inactive_text,
                            fill="white", font=("Segoe UI", 16, "bold"), justify="center")

        self.overlays[monitor['id']] = {
            'window': overlay,
            'canvas': canvas,
            'image_item': image_item,
            'animation_id': None
        }
        self.root.after(10, self._animate_static_effect, monitor['id'])

    def _animate_static_effect(self, monitor_id):
        if not self.is_running or monitor_id not in self.overlays:
            return

        overlay_info = self.overlays[monitor_id]
        canvas = overlay_info['canvas']

        if not canvas.winfo_exists():
            return

        w, h = overlay_info['window'].winfo_width(), overlay_info['window'].winfo_height()
        if w <= 1 or h <= 1:
            self.root.after(50, self._animate_static_effect, monitor_id)
            return

        try:
            tile_size = 128
            noise_pattern = np.random.randint(0, 35, (tile_size, tile_size), dtype=np.uint8)
            noise_pil = Image.fromarray(noise_pattern, 'L')
            full_img = Image.new('L', (w, h))
            for y in range(0, h, tile_size):
                for x in range(0, w, tile_size):
                    full_img.paste(noise_pil, (x, y))

            new_photo = ImageTk.PhotoImage(image=full_img)
            canvas.itemconfig(overlay_info['image_item'], image=new_photo)
            canvas.image_ref = new_photo

            animation_id = self.root.after(100, self._animate_static_effect, monitor_id)
            self.overlays[monitor_id]['animation_id'] = animation_id
        except Exception as e:
            print(f"Error during static animation: {e}")
