import logging
from aiogram.utils import executor
from src.handlers import common
from src.database import postgres
from bot_init import dp


async def on_startup(_):
    """Connect to database during bot launch."""
    await postgres.asyncpg_connect()
    logger.info('Bot has been successfully launched!')


async def on_shutdown(_):
    """Disconnect from database during bot shutdown."""
    await postgres.asyncpg_close()
    logger.info('Bot has been successfully shut down!')


def main():
    # Register handlers
    common.register_handlers(dp)

    # Launch bot
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)


if __name__ == '__main__':
    # Add logging
    logging.basicConfig(handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()],
                        level=logging.INFO,
                        format='[%(asctime)s: %(levelname)s: %(name)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        encoding='utf-8')
    logger = logging.getLogger(__name__)

    main()
