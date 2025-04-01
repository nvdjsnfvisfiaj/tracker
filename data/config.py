import configparser
import os
from pathlib import Path

config_path = Path(__file__).parent.parent / "config.ini"

config = configparser.ConfigParser()

if os.path.exists(config_path):
    config.read(config_path)
else:
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

BOT_TOKEN = config.get('Telegram', 'BOT_TOKEN')
API_ID = config.getint('Telegram', 'API_ID')
API_HASH = config.get('Telegram', 'API_HASH')
PHONE_NUMBER = config.get('Telegram', 'PHONE_NUMBER')
CHANNEL_ID = config.getint('Telegram', 'CHANNEL_ID')
