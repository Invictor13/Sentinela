import sys
import os
import re

def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se _MEIPASS não existir, estamos no modo de desenvolvimento normal
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def is_valid_foldername(name):
    """Verifica se um nome de pasta é válido, evitando caracteres proibidos."""
    if not name:
        return False
    # Procura por qualquer um dos caracteres inválidos em nomes de arquivo/pasta do Windows
    if re.search(r'[<>:"/\\|?*]', name):
        return False
    return True
