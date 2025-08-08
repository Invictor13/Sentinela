import tkinter as tk
from tkinter import Toplevel

class PreparationIndicator(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.animation_id = None
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.withdraw()
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        # To be populated by the calling module if needed
        self.module_instance = None
        self.active_monitor_for_recording = None # Legacy for `show` method

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_preparation_mode(self, monitor_geom, text=""):
        self._clear_container()
        self.container.configure(bg='#2b2b2b', padx=10, pady=5)

        prep_label = tk.Label(self.container, text="● Preparando", font=("Segoe UI", 12, "bold"), fg="#ffcc00", bg=self.container.cget('bg'))
        prep_label.pack(side="left", padx=(0, 10))

        info_label = tk.Label(self.container, text=text, font=("Segoe UI", 10), fg="white", bg=self.container.cget('bg'))
        info_label.pack(side="left", padx=(0, 15))

        self._display_window(monitor_geom)

    def hide_preparation_mode(self):
        self.withdraw()

    def flash_success(self):
        """Flashes the indicator green to show a successful capture."""
        if not self.winfo_exists():
            return

        original_bg = self.container.cget('bg')
        original_prep_fg = self.container.winfo_children()[0].cget('fg') # Assuming first child is the "● Preparando" label

        self.container.configure(bg='green')
        for widget in self.container.winfo_children():
            widget.configure(bg='green')

        def restore_colors():
            if self.winfo_exists():
                self.container.configure(bg=original_bg)
                # Restore original colors of all children
                self.container.winfo_children()[0].configure(fg=original_prep_fg, bg=original_bg)
                for child in self.container.winfo_children()[1:]:
                    child.configure(bg=original_bg)

        self.after(150, restore_colors)

    def _display_window(self, monitor_geom):
        if not monitor_geom: return
        self.update_idletasks()
        x = monitor_geom['left'] + monitor_geom['width'] - self.winfo_reqwidth() - 20
        y = monitor_geom['top'] + 20
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.animation_id = None
        self.withdraw()

    # --- Legacy methods for ScreenRecordingModule ---
    # This part remains to avoid breaking the recording functionality,
    # but ideally, it would be in its own `RecordingStateIndicator` class.

    def show(self, monitor_geom):
        """ Mostra o indicador no modo de gravação normal. """
        self._clear_container()
        self.container.configure(bg='#2b2b2b', padx=10, pady=5)

        self.rec_label = tk.Label(self.container, text="REC", font=("Segoe UI", 12, "bold"), fg="#ff0000", bg=self.container.cget('bg'))
        self.rec_label.pack(side="left", padx=(0, 10))

        self.time_label = tk.Label(self.container, text="00:00:00", font=("Segoe UI", 12, "bold"), fg="white", bg=self.container.cget('bg'))
        self.time_label.pack(side="left", padx=(0, 10))

        self.info_label = tk.Label(self.container, text="F10 para parar", font=("Segoe UI", 10), fg="white", bg=self.container.cget('bg'))
        self.info_label.pack(side="left", padx=(0, 15))

        stop_button = tk.Button(self.container, text="PARAR", font=("Segoe UI", 9, "bold"), fg="white", bg="#c70000", relief="flat",
                                command=self.module_instance.stop_recording, bd=0, padx=10, pady=2)
        stop_button.pack(side="left", padx=(0, 5))

        self.update_time(0)
        self._display_window(monitor_geom)
        if self.animation_id is None:
            self._animate_rec()

    def _animate_rec(self):
        if not self.winfo_exists() or not (self.module_instance and self.module_instance.is_recording):
            if self.animation_id:
                self.after_cancel(self.animation_id)
                self.animation_id = None
            return

        current_color = self.rec_label.cget("fg")
        new_color = self.cget('bg') if current_color == '#ff0000' else '#ff0000'
        self.rec_label.config(fg=new_color)
        self.animation_id = self.after(700, self._animate_rec)

    def update_time(self, elapsed_seconds):
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            secs = int(elapsed_seconds)
            mins, secs = divmod(secs, 60)
            hrs, mins = divmod(mins, 60)
            self.time_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
