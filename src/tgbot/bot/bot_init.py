import os
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


storage = MemoryStorage()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot, storage=storage)
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
LOCALIZATION_LANGUAGE = os.getenv('LOCALIZATION_LANGUAGE')
TIMEZONE = os.getenv('TZ')
IMAGES_ROWS = int(os.getenv('IMAGES_ROWS'))
IMAGES_COLS = int(os.getenv('IMAGES_COLS'))
IMAGES_NUMBER = IMAGES_ROWS * IMAGES_COLS
SCORE_BASIC = float(os.getenv('SCORE_BASIC'))
STAGES_NUMBER = int(os.getenv('STAGES_NUMBER'))
