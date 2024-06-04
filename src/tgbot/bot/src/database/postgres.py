import asyncpg
import datetime
import logging
from decimal import Decimal
from bot_init import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB


logger = logging.getLogger(__name__)
conn: asyncpg.Connection


async def asyncpg_connect() -> None:
    """Initialize asyncpg connection."""
    global conn
    conn = await asyncpg.connect(host='database', database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)

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


async def is_subscription_active(telegram_id: int) -> bool | None:
    """Check subcription's expiration date of client with specified telegram_id. Return TRUE if acive, NONE if inactive."""
    return await conn.fetchval(
        '''
        SELECT TRUE
        FROM subscriptions_clients AS sc
        JOIN clients AS c
        ON sc.client_id = c.id
        WHERE c.telegram_id = $1
        AND sc.expiration_date > NOW();
        ''',
        telegram_id
    )


async def is_subscription_blank(telegram_id: int) -> bool | None:
    """Check subscription was never paid or renewed."""
    return await conn.fetchval(
        '''
        SELECT TRUE
        FROM subscriptions_clients AS sc
        JOIN clients AS c
        ON sc.client_id = c.id
        WHERE c.telegram_id = $1
        AND sc.expiration_date IS NULL;
        ''',
        telegram_id
    )


async def get_clients_ids() -> list[asyncpg.Record]:
    """Return all clients' ids from DB as list[asyncpg.Record]."""
    return await conn.fetch(
        '''
        SELECT id
        FROM clients;
        '''
    )


async def get_clients_telegram_ids() -> list[asyncpg.Record]:
    """Return all clients' telegram ids from DB as list[asyncpg.Record]."""
    return await conn.fetch(
        '''
        SELECT telegram_id
        FROM clients;
        '''
    )


async def get_clientID_by_telegramID(telegram_id: int) -> int | None:
    """Return client_id by specified telegram_id."""
    return await conn.fetchval('''
        SELECT id
        FROM clients
        WHERE telegram_id = $1;
        ''',
        telegram_id
    )


async def get_telegramID_by_username(username: str) -> int | None:
    """Return telegram_id by specified @username."""
    return await conn.fetchval(
        '''
        SELECT telegram_id
        FROM clients
        WHERE username = $1;
        ''',
        username
    )


async def get_client_info_by_telegramID(telegram_id: int) -> asyncpg.Record | None:
    """Return information about client by specified telegram_id.

    :param telegram_id:
    :return: asyncgp.Record object having (id, name, surname, username, register_date)
    :rtype: asyncpg.Record | None
    """
    return await conn.fetchrow(
        '''
        SELECT id, name, surname, username, register_date
        FROM clients
        WHERE telegram_id = $1;
        ''',
        telegram_id
    )


async def get_client_info_by_clientID(client_id: int) -> asyncpg.Record | None:
    """Return information about client by specified client_id.

    :param client_id:
    :return: asyncgp.Record object having (name, surname, username, telegram_id, register_date)
    :rtype: asyncpg.Record | None
    """
    return await conn.fetchrow(
        '''
        SELECT name, surname, username, telegram_id, register_date
        FROM clients
        WHERE id = $1;
        ''',
        client_id
    )


async def get_subscription_info_by_clientID(client_id: int) -> asyncpg.Record | None:
    """Return information about subscription of client specified by client_id.

    :param client_id:
    :return: asyncgp.Record object having (sub_id, title, description)
    :rtype: asyncpg.Record | None
    """
    return await conn.fetchrow(
        '''
        SELECT sub.id, sub.title, sub.description
        FROM subscriptions_clients AS sub_clients
        JOIN subscriptions AS sub
        ON sub.id = sub_clients.sub_id
        WHERE sub_clients.client_id = $1;
        ''',
        client_id
    )


async def get_subscription_prices_info(subscription_id: int) -> list[asyncpg.Record] | None:
    """Return information about subscription days number with prices by specified subscription_id.

    :param subscription_id:
    :return: list of asyncgp.Record objects having (days_number, price)
    :rtype: list[asyncpg.Record] | None
    """
    return await conn.fetch(
        '''
        SELECT days_number, price
        FROM subscriptions_prices
        WHERE sub_id = $1;
        ''',
        subscription_id
    )


async def get_subscription_prices_main_info(subscription_id: int) -> asyncpg.Record | None:
    """Return information about main (minimal) subscription days number with prices by specified subscription_id.

    :param subscription_id:
    :return: asyncgp.Record objects having (days_number, price)
    :rtype: asyncpg.Record | None
    """
    return await conn.fetchrow(
        '''
        SELECT days_number, price
        FROM subscriptions_prices
        WHERE sub_id = $1
        ORDER BY days_number ASC
        LIMIT 1;
        ''',
        subscription_id
    )


async def get_subscription_expiration_date(telegram_id: int) -> datetime.datetime | None:
    """Return subsctiption's expiration date in datetime.datetime format."""
    return await conn.fetchval(
        '''
        SELECT sc.expiration_date
        FROM subscriptions_clients AS sc
        JOIN clients AS c
        ON sc.client_id = c.id
        WHERE c.telegram_id = $1;
        ''',
        telegram_id
    )


async def get_payment_status(payment_id: int) -> bool | None:
    """Return TRUE if payment was successful else NONE."""
    return await conn.fetchval(
        '''
        SELECT is_successful
        FROM payments
        WHERE id = $1;
        ''',
        payment_id
    )

async def get_payment_days_number(payment_id: int) -> int | None:
    """Return paid days number for specified payment_id."""
    return await conn.fetchval(
        '''
        SELECT days_number
        FROM payments
        WHERE id = $1;
        ''',
        payment_id
    )


async def get_payments_successful_sum(client_id: int) -> Decimal:
    """Return sum of successful payments initiated by client."""
    return await conn.fetchval(
        '''
        SELECT
        CASE
            WHEN SUM(price) IS NULL THEN 0.00
            ELSE SUM(price)
        END
        FROM payments
        WHERE client_id = $1
        AND is_successful = TRUE;
        ''',
        client_id)


async def get_earnings_per_month() -> Decimal:
    """Return sum of successful payments' prices per current month."""
    return await conn.fetchval(
        '''
        SELECT COALESCE(SUM(price), 0)
        FROM payments
        WHERE is_successful = TRUE
        AND initiation_date > date_trunc('month', CURRENT_TIMESTAMP);
        '''
    )
        

async def insert_payment(client_id: int, sub_id: int, price: float, days_number: int) -> int | None:
    """Add new payment for client in DB."""
    return await conn.fetchval(
        '''
        INSERT INTO payments (client_id, sub_id, price, days_number)
        VALUES($1, $2, $3, $4)
        RETURNING id;
        ''',
        client_id, sub_id, price, days_number
    )


async def update_payment_successful(payment_id: int, client_id: int, paid_days: int) -> None:
    """Change status of payment specified by payment_id to successful and change subscription data."""
    async with conn.transaction():
        await conn.execute(
            '''
            UPDATE payments
            SET is_successful = TRUE
            WHERE id = $1;
            ''',
            payment_id
        )

        await conn.execute(
            '''
            UPDATE subscriptions_clients
            SET expiration_date =
            CASE
                WHEN expiration_date IS NULL THEN CURRENT_TIMESTAMP + make_interval(days => $1)
                ELSE expiration_date + make_interval(days => $1)
            END
            WHERE client_id = $2;
            ''',
            paid_days, client_id
        )
        