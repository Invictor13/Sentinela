import configparser
import os

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
    if 'Paths' not in config:
        config['Paths'] = {'DefaultSaveLocation': DEFAULT_SAVE_LOCATION_FALLBACK}
    current_save_location = config.get('Paths', 'DefaultSaveLocation', fallback=DEFAULT_SAVE_LOCATION_FALLBACK)
    os.makedirs(current_save_location, exist_ok=True)
    return {"DefaultSaveLocation": current_save_location, "config_parser_obj": config}

def save_app_config(config_parser_obj, save_path_to_save):
    config_parser_obj['Paths']['DefaultSaveLocation'] = save_path_to_save
    with open(CONFIG_FILE, 'w') as configfile:
        config_parser_obj.write(configfile)
