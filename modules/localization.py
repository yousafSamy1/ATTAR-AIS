
import os
from modules.translations import TRANSLATIONS

# Get absolute path for the language file to avoid CWD issues
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG_FILE = os.path.join(BASE_DIR, "last_lang.txt")

def get_saved_lang():
    try:
        if os.path.exists(LANG_FILE):
            with open(LANG_FILE, "r") as f:
                lang = f.read().strip()
                if lang in TRANSLATIONS:
                    return lang
    except Exception as e:
        print(f"Lang read error: {e}")
    return 'ar'

# Keep for compatibility with existing imports
CURRENT_LANG = get_saved_lang()

def save_lang(lang):
    global CURRENT_LANG
    CURRENT_LANG = lang
    with open(LANG_FILE, "w") as f:
        f.write(lang)

def tr(key):
    # DYNAMIC FETCH to prevent stale language states in long-running processes
    lang = get_saved_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
