from pynput import keyboard

def key_listener_thread_proc(capture_module, recording_module, root_window):
    # Teclas de função para captura e gravação.
    CAPTURE_KEY = keyboard.Key.f9
    RECORD_KEY = keyboard.Key.f10

    def on_press(key):
        # Verifica se a tecla para captura de tela foi pressionada.
        if key == CAPTURE_KEY:
            # A captura de tela só pode ser iniciada se não houver uma gravação em andamento.
            if not recording_module.is_recording:
                root_window.after(0, capture_module.start_capture_mode)

        # Verifica se a tecla para gravação foi pressionada.
        elif key == RECORD_KEY:
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

    # O on_release não é mais necessário para a lógica de teclas simples.
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
