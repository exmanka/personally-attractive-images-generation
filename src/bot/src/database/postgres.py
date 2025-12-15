import asyncpg
import logging
from bot_init import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB


logger = logging.getLogger(__name__)
conn: asyncpg.Connection


async def asyncpg_connect() -> None:
    """Initialize asyncpg connection."""
    global conn
    conn = await asyncpg.connect(host='postgres', database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)

    if conn:
        logger.info('Database has been successfully connected!')


async def asyncpg_close() -> None:
    """Close asyncpg connection."""
    await conn.close()

    if conn.is_closed():
        logger.info('Database has been successfully disconnected!')


async def insert_user(name: str,
                        telegram_id: int,
                        sex: str,
                        surname: str | None = None,
                        username: str | None = None,
                        ) -> int:
    """Add new client to database."""
    if username:
        username = '@' + username

    
    return await conn.fetchval(
        '''
        INSERT INTO users (name, surname, username, telegram_id, sex)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id;
        ''',
        name, surname, username, telegram_id, sex
    )


async def is_user_registered(telegram_id: int) -> bool | None:
    """Return TRUE if user exists in database else NONE."""
    return await conn.fetchval(
        '''
        SELECT TRUE
        FROM users
        WHERE telegram_id = $1;
        ''',
        telegram_id
    )
