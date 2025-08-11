import configparser
from pynput import keyboard
from src.config.settings import CONFIG_FILE

def parse_hotkey_string(hotkey_string):
    """
    Parses a user-friendly hotkey string (e.g., "Shift + F9")
    into a pynput-compatible format (e.g., "<shift>+<f9>").
    """
    parts = [part.strip().lower() for part in hotkey_string.split('+')]

    # Map common names to pynput names
    key_map = {
        'ctrl': 'ctrl_l',
        'shift': 'shift',
        'alt': 'alt_l',
        # Special keys that might be written as text
        'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
        'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
        'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
    }

    pynput_parts = []
    for part in parts:
        if part in key_map:
            pynput_parts.append(f"<{key_map[part]}>")
        elif len(part) == 1: # Regular character key
            pynput_parts.append(part)
        else: # Likely a special key like 'Home', 'Insert', etc. which pynput understands as is
             pynput_parts.append(f"<{part}>")


    return "+".join(pynput_parts)


def key_listener_thread_proc(capture_module, recording_module, root_window, main_app_instance):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    capture_hotkey_str = config.get('Hotkeys', 'capture', fallback='F9')
    record_hotkey_str = config.get('Hotkeys', 'record', fallback='F10')

    def on_activate_capture():
        # Logic as per the new blueprint
        # This check needs to be based on the recording module's state attribute
        if recording_module.is_recording:
            return

        if not capture_module.is_in_session:
            # Inicia a sessão
            root_window.after(0, capture_module.start_capture_session)
        else:
            # Tira o screenshot dentro da sessão
            # The 'get_active_monitor_logic' is implemented by the capture module's overlay
            active_monitor = capture_module.overlay_manager.get_active_monitor() # Pega a tela ativa
            if active_monitor:
                root_window.after(0, capture_module.take_screenshot, active_monitor)

    def on_activate_record():
        # Prevent recording from starting if a capture is in preparation.
        if capture_module.is_in_session:
            return

        # This check is illustrative. Assuming is_recording is a boolean property.
        # The actual state transition logic for recording remains unchanged.
        if recording_module.state == "idle":
            record_all = main_app_instance.record_all_screens_var.get()
            root_window.after(0, recording_module.enter_preparation_mode, record_all)
        elif recording_module.state == "preparing":
            root_window.after(0, recording_module.start_recording_mode)
        elif recording_module.state == "recording":
            root_window.after(0, recording_module.stop_recording)

    # It's better to handle exceptions here in case of invalid hotkey formats
    try:
        parsed_capture_hotkey = parse_hotkey_string(capture_hotkey_str)
        parsed_record_hotkey = parse_hotkey_string(record_hotkey_str)

        def on_escape():
            """Cancels any active preparation mode."""
            if capture_module.is_in_session:
                root_window.after(0, capture_module.end_capture_session)
            elif recording_module.is_preparing:
                root_window.after(0, recording_module.exit_preparation_mode)

        hotkeys = {
            parsed_capture_hotkey: on_activate_capture,
            parsed_record_hotkey: on_activate_record,
            '<esc>': on_escape
        }

        with keyboard.GlobalHotKeys(hotkeys) as h:
            h.join()

    except Exception as e:
        print(f"Erro ao registrar os atalhos de teclado: {e}")
        # Optionally, show an error to the user on the main thread
        # root_window.after(0, lambda: messagebox.showerror("Erro de Atalho", f"Não foi possível registrar os atalhos: {e}"))
        # For now, we just print to console to avoid crashing the app.
        pass
