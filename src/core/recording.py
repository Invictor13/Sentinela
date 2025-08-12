def recording_thread(self):
        """A thread que realiza a captura e escrita dos frames de vídeo, sem omissões."""
        
        # --- 1. PREPARAÇÃO DA ÁREA DE CAPTURA E DIMENSÕES ---
        
        capture_area = {}
        width, height = 0, 0

        with mss.mss() as sct:
            if self.record_all_screens:
                print("Modo Onipresente: Calculando dimensões de todas as telas.")
                # Calcula a largura total e a altura máxima de todos os monitores
                total_width = sum(m['width'] for m in sct.monitors[1:])
                max_height = max(m['height'] for m in sct.monitors[1:])
                width, height = total_width, max_height
                # A área de captura para múltiplas telas será gerenciada frame a frame
            else:
                print("Modo Focado: Usando dimensões da tela única selecionada.")
                if self.target_monitor:
                    capture_area = self.target_monitor
                    width, height = capture_area['width'], capture_area['height']
                else:
                    print("ERRO: Nenhum monitor alvo definido para gravação focada.")
                    self.is_recording = False
                    return

        # --- 2. CASCATA DE CONTINGÊNCIA DE CODECS ---
        
        config = self.app_config
        quality_profile = config.get('Recording', 'quality', fallback='high')
        
        # Define FPS e dimensões com base no perfil
        if quality_profile == 'high':
            rec_fps = 15.0
            rec_width, rec_height = width, height
        else: # compact (web)
            rec_fps = 10.0
            # Redimensiona para 720p mantendo o aspect ratio
            aspect_ratio = width / height
            rec_height = 720
            rec_width = int(rec_height * aspect_ratio)

        # Garante que as dimensões finais sejam números pares
        if rec_width % 2 != 0: rec_width -= 1
        if rec_height % 2 != 0: rec_height -= 1

        filename_base = f"Evidencia_Gravacao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        save_path = self.app_config.get('Paths', 'DefaultSaveLocation')
        self.out = None
        final_video_path = ""

        # NÍVEL 1: Tenta MP4/H.264 (se a qualidade for alta)
        if quality_profile == 'high':
            try:
                print("NÍVEL 1: Tentando codec de ALTA QUALIDADE (MP4/avc1)...")
                path = os.path.join(save_path, f"{filename_base}.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                self.out = cv2.VideoWriter(path, fourcc, rec_fps, (rec_width, rec_height))
                if not self.out.isOpened(): raise IOError("MP4/avc1 falhou ao abrir.")
                final_video_path = path
            except Exception as e:
                print(f"AVISO: Falha no Nível 1. {e}")
                self.out = None

        # NÍVEL 2: Tenta WebM/VP9 (se Nível 1 falhou ou a qualidade é web)
        if self.out is None:
            try:
                print("NÍVEL 2: Tentando codec OTIMIZADO PARA WEB (WebM/VP9)...")
                path = os.path.join(save_path, f"{filename_base}.webm")
                fourcc = cv2.VideoWriter_fourcc(*'VP90')
                self.out = cv2.VideoWriter(path, fourcc, rec_fps, (rec_width, rec_height))
                if not self.out.isOpened(): raise IOError("WebM/VP9 falhou ao abrir.")
                final_video_path = path
            except Exception as e:
                print(f"AVISO: Falha no Nível 2. {e}")
                self.out = None

        # NÍVEL 3: Tenta AVI/MJPG (fallback final)
        if self.out is None:
            try:
                print("NÍVEL 3: Ativando fallback de MÁXIMA COMPATIBILIDADE (AVI/MJPG)...")
                path = os.path.join(save_path, f"{filename_base}.avi")
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                self.out = cv2.VideoWriter(path, fourcc, rec_fps, (rec_width, rec_height))
                if not self.out.isOpened(): raise IOError("AVI/MJPG falhou ao abrir.")
                final_video_path = path
            except Exception as e:
                self.out = None
        
        if not self.out or not self.out.isOpened():
            messagebox.showerror("Erro Crítico de Gravação", "O Sentinela não conseguiu ativar nenhum codec de vídeo em seu sistema.")
            self.root.after(0, self.stop_recording)
            return

        # --- 3. O LOOP PRINCIPAL DE GRAVAÇÃO ---
        
        print("Iniciando loop de captura de frames...")
        # AQUI PRECISA DO INDICADOR DE GRAVAÇÃO ATIVA, NÃO O DE PREPARAÇÃO
        # Supondo que você tenha um `active_recording_indicator`
        # self.active_recording_indicator.show()

        with mss.mss() as sct:
            while self.is_recording:
                loop_start_time = time.time()
                try:
                    # --- Feitiço de Invisibilidade (para o indicador de gravação ativa) ---
                    # self.active_recording_indicator.withdraw()
                    # time.sleep(0.01) # Pequena pausa para garantir a renderização

                    if self.record_all_screens:
                        # Costura os frames de todas as telas
                        combined_frame_np = np.zeros((height, width, 3), dtype=np.uint8)
                        current_x_offset = 0
                        for monitor in sct.monitors[1:]:
                            sct_img = sct.grab(monitor)
                            frame_np = np.array(sct_img)
                            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)
                            combined_frame_np[:, current_x_offset:current_x_offset + monitor['width']] = frame_bgr
                            current_x_offset += monitor['width']
                        
                        final_frame = combined_frame_np
                    else:
                        # Captura apenas a tela única
                        sct_img = sct.grab(capture_area)
                        frame_np = np.array(sct_img)
                        final_frame = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)

                    # --- Mostra o indicador novamente ---
                    # self.active_recording_indicator.deiconify()

                    # Redimensiona o frame final se necessário
                    if (final_frame.shape[1], final_frame.shape[0]) != (rec_width, rec_height):
                        frame_to_write = cv2.resize(final_frame, (rec_width, rec_height), interpolation=cv2.INTER_AREA)
                    else:
                        frame_to_write = final_frame

                    # Escreve o frame no arquivo de vídeo
                    self.out.write(frame_to_write)

                    # Garante a taxa de quadros correta
                    elapsed_time = time.time() - loop_start_time
                    sleep_time = (1.0 / rec_fps) - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                except Exception as e:
                    print(f"Erro durante o loop de gravação: {e}")
                    self.is_recording = False # Encerra o loop em caso de erro

        # --- 4. FINALIZAÇÃO ---
        
        print("Finalizando o arquivo de vídeo...")
        if self.out:
            self.out.release()
        
        # self.active_recording_indicator.hide()

        # Mostra a mensagem de sucesso na thread principal
        if os.path.exists(final_video_path) and os.path.getsize(final_video_path) > 0:
            self.root.after(0, lambda: show_success_dialog(self.root, "Gravação salva com sucesso!", os.path.dirname(final_video_path), final_video_path))
        
        print("Thread de gravação finalizada.")
