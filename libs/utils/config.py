"""Android 适配配置管理"""

import os
import json
from pathlib import Path

APP_NAME = "私人日记"
APP_VERSION = "0.1.0"

# Android 内部存储路径
DATA_DIR = Path(os.environ.get("ANDROID_APP_PATH",
                                os.path.join(os.path.expanduser("~"), ".private-diary")))
DATABASE_PATH = DATA_DIR / "diary.db"
CONFIG_PATH = DATA_DIR / "config.json"
BACKUP_DIR = DATA_DIR / "backups"

DEFAULT_CONFIG = {
    "theme": "light",
    "font_size": 16,
    "reminder_enabled": True,
    "reminder_auto_learn": True,
    "auto_save_seconds": 60,
    "recommendation_enabled": True,
    "biometric_enabled": False,
}

SECURITY_CONFIG = {
    "min_password_length": 6,
    "max_login_attempts": 5,
    "lockout_duration_seconds": 300,
    "pbkdf2_iterations": 600000,
    "pbkdf2_hash_algorithm": "sha256",
    "aes_key_size": 256,
    "iv_length": 12,
}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_data_dir()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(saved)
            return config
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    ensure_data_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_config(key: str, default=None):
    config = load_config()
    return config.get(key, default)


def set_config(key: str, value):
    config = load_config()
    config[key] = value
    save_config(config)
