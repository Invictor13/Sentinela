# Este é o grimório comum, um lugar para feitiços e utilitários compartilhados.
import sys
import os

def resource_path(relative_path):
    """ Obtém o caminho absoluto para um recurso, funciona para dev e para o PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver no modo PyInstaller, use o caminho do arquivo
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, "assets", relative_path)
