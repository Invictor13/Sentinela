from pynput import keyboard

def key_listener_thread_proc(capture_module, recording_module, root_window):
    current_keys = set()
    # Combinações de teclas para captura de tela e gravação.
    CAPTURE_COMBO = {keyboard.Key.ctrl, keyboard.Key.f9}
    RECORD_COMBO = {keyboard.Key.ctrl, keyboard.Key.f10}

    def on_press(key):
        # Adiciona a tecla pressionada ao conjunto de teclas atuais.
        if key in {keyboard.Key.ctrl, keyboard.Key.f9, keyboard.Key.f10}:
            current_keys.add(key)

        # Verifica se a combinação para captura de tela foi pressionada.
        if CAPTURE_COMBO.issubset(current_keys):
            # A captura de tela só pode ser iniciada se não houver uma gravação em andamento.
            if not recording_module.is_recording:
                root_window.after(0, capture_module.start_capture_mode)

        # Verifica se a combinação para gravação foi pressionada.
        elif RECORD_COMBO.issubset(current_keys):
            # A lógica de gravação não deve interferir na captura de tela.
            if capture_module.capturing:
                return

            state = recording_module.state
            if state == "idle":
                root_window.after(0, recording_module.enter_preparation_mode)
            elif state == "preparing":
                root_window.after(0, recording_module.start_recording_mode)
            elif state == "recording":
                root_window.after(0, recording_module.stop_recording)

    def on_release(key):
        # Garante que a tecla Ctrl+F9 não fique "presa" se F10 for liberado primeiro.
        if key == keyboard.Key.ctrl and keyboard.Key.f10 not in current_keys:
             current_keys.clear()

        try:
            current_keys.remove(key)
        except KeyError:
            pass

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
