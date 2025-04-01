import logging
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.dispatcher.dispatcher import Dispatcher
from pyrogram import Client

from data.config import API_ID, API_HASH, BOT_TOKEN, PHONE_NUMBER


class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return f"[{super().formatTime(record, '%b %d, %Y %H:%M:%S')}]"


root_dir = Path(__file__).parent.parent
logs_dir = root_dir / "data" / "logs"
log_file = logs_dir / "bot.log"

logging.basicConfig(
    level=logging.ERROR,
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler()
    ]
)

formatter = CustomFormatter('%(asctime)s - %(name)s - [%(levelname)s]: %(message)s')
for handler in logging.root.handlers:
    handler.setFormatter(formatter)

logger = logging.getLogger('tracker')
logger.setLevel(logging.INFO)

bot_logger = logging.getLogger('aiogram.dispatcher')
bot_logger.setLevel(logging.INFO)
client_logger = logging.getLogger('pyrogram')

bot_logger.setLevel(logging.INFO)
client_logger.setLevel(logging.WARNING)

session_path = Path(__file__).parent.parent / "data" / "account"

telegram_client = Client(
    name=str(session_path),
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode='HTML',
        link_preview_is_disabled=False
    )
)
dp = Dispatcher()
