from pynput import keyboard

def key_listener_thread_proc(capture_module, recording_module, root_window):
    current_keys = set()
    CAPTURE_COMBO = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.Key.f9}
    RECORD_COMBO = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.Key.f10}

    def on_press(key):
        if key in {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.Key.f9, keyboard.Key.f10}:
            current_keys.add(key)

        if CAPTURE_COMBO.issubset(current_keys):
            if capture_module.capturing:
                root_window.after(0, capture_module.take_screenshot)
            elif not recording_module.is_recording:
                root_window.after(0, capture_module.start_capture_mode)
        elif RECORD_COMBO.issubset(current_keys):
            if recording_module.is_recording:
                root_window.after(0, recording_module.stop_recording)
            elif not capture_module.capturing:
                root_window.after(0, recording_module.open_recording_selection_ui)

    def on_release(key):
        try:
            current_keys.remove(key)
        except KeyError:
            pass

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
