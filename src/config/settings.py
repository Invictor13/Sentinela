import configparser
import os

CONFIG_FILE = "config.ini"
USER_DOCUMENTS_PATH = os.path.join(os.path.expanduser("~"), "Documents")
DEFAULT_SAVE_LOCATION_FALLBACK = os.path.join(USER_DOCUMENTS_PATH, "SentinelaEvidencias")

def load_app_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # --- Setup default values if file or sections are missing ---
    if not config.has_section('Paths'):
        config.add_section('Paths')
        config.set('Paths', 'DefaultSaveLocation', DEFAULT_SAVE_LOCATION_FALLBACK)

    if not config.has_section('Recording'):
        config.add_section('Recording')
        config.set('Recording', 'Quality', 'high')

    if not config.has_section('Hotkeys'):
        config.add_section('Hotkeys')
        config.set('Hotkeys', 'capture', 'F9')
        config.set('Hotkeys', 'record', 'F10')

    if not config.has_section('User'):
        config.add_section('User')
        config.set('User', 'has_run_before', 'false')

    # --- Read values ---
    current_save_location = config.get('Paths', 'DefaultSaveLocation', fallback=DEFAULT_SAVE_LOCATION_FALLBACK)
    recording_quality = config.get('Recording', 'Quality', fallback='high')
    capture_hotkey = config.get('Hotkeys', 'capture', fallback='F9')
    record_hotkey = config.get('Hotkeys', 'record', fallback='F10')
    has_run_before = config.getboolean('User', 'has_run_before', fallback=False)

    os.makedirs(current_save_location, exist_ok=True)

    # --- Write back any missing values ---
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

    return {
        "DefaultSaveLocation": current_save_location,
        "RecordingQuality": recording_quality,
        "CaptureHotkey": capture_hotkey,
        "RecordHotkey": record_hotkey,
        "HasRunBefore": has_run_before,
        "config_parser_obj": config
    }

def save_app_config(config_parser_obj, save_path, quality, capture_hotkey, record_hotkey):
    # Ensure sections exist
    if not config_parser_obj.has_section('Paths'): config_parser_obj.add_section('Paths')
    if not config_parser_obj.has_section('Recording'): config_parser_obj.add_section('Recording')
    if not config_parser_obj.has_section('Hotkeys'): config_parser_obj.add_section('Hotkeys')

    # Set values
    config_parser_obj.set('Paths', 'DefaultSaveLocation', save_path)
    config_parser_obj.set('Recording', 'Quality', quality)
    config_parser_obj.set('Hotkeys', 'capture', capture_hotkey)
    config_parser_obj.set('Hotkeys', 'record', record_hotkey)

    with open(CONFIG_FILE, 'w') as configfile:
        config_parser_obj.write(configfile)
