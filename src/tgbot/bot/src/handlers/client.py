import logging
import datetime
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from src.middlewares import client_mw
from src.keyboards import client_kb
from src.states import client_fsm
from src.database import postgres
from src.services import internal, api_gateway, localization as loc


logger = logging.getLogger(__name__)


@client_mw.clients_only()
async def sub_renewal_payment_inline(call: CallbackQuery):
    """Create payment link and send message with inline payment link, payment check and payment cancel."""
    days_number = int(call.data.split('-')[1])
    await call.answer()
    await internal.send_payment(call.from_user.id, call.message.chat.id, call.message.message_id, days_number)


@client_mw.clients_only()
async def sub_renewal_menu_inline(msg: Message):
    """Send message with inline payment menu."""
    await internal.show_payment_menu_inline(msg.from_user.id)


@client_mw.clients_only()
async def sub_status(msg: Message):
    """Send messages with information about subscription status."""
    # If subscription is acive
    if await postgres.is_subscription_active(msg.from_user.id):
        await msg.answer(loc.client.msgs['sub_active'], parse_mode='HTML')

    # If subsctiption is inactive
    else:
        await msg.answer(loc.client.msgs['sub_inactive'], parse_mode='HTML')

    await msg.answer(loc.client.msgs['sub_expiration_date'].\
                     format(await internal.convert_datetime(await postgres.get_subscription_expiration_date(msg.from_user.id))),
                     parse_mode='HTML')


@client_mw.active_sub_only()
async def interfax_test(msg: Message):
    """Get information from algo microservice."""
    await msg.answer('Тут уже ничего нет')
    

@client_mw.active_sub_only()
async def moscow_exchange_test(msg: Message):
    """Get information from parsers microservice."""
    status_code, data = await api_gateway.get('http://app-parsers:8000/data', __name__)

    # If HTTP status is 200 (OK)
    if status_code == 200:
        await msg.answer(data)

    # If got another HTTP status
    else:
        await msg.answer(loc.internal.msgs['http-error'].format(status_code))

    # companies_info: list = await postgres_dbms.get_companies_info()
    # for _, company_name, company_update_date, company_download_url in companies_info:
    #     await msg.answer(loc.client.msgs['company_info'].format(company_name, company_update_date, company_download_url), 'HTML')


@client_mw.clients_only()
async def sub_renewal_verification(call: CallbackQuery):
    """Verify client's payment."""
    payment_id = int(call.data.split('-')[2])
    is_subscription_blank = bool(await postgres.is_subscription_blank(call.from_user.id))
    await internal.sub_renewal_verification(call.from_user.id, call.message.chat.id, call.message.message_id,
                                            payment_id, is_subscription_blank)
    await call.answer()
    

@client_mw.clients_only()
async def sub_renewal_cancel(call: CallbackQuery):
    """Delete message with payment link."""
    await call.message.answer(loc.client.msgs['payment_cancel'], 'HTML')
    await call.answer()
    await call.message.delete()
    

def register_handlers(dp: Dispatcher):
    """Register client handlers in dispatcher."""
    dp.register_message_handler(sub_renewal_menu_inline, Text(loc.client.btns['sub_renewal']))
    dp.register_message_handler(sub_status, Text(loc.client.btns['sub_status']))
    dp.register_message_handler(interfax_test, Text(loc.client.btns['interfax_test']))
    dp.register_message_handler(moscow_exchange_test, Text(loc.client.btns['moscow_exchange_test']))
    dp.register_callback_query_handler(sub_renewal_cancel, lambda call: call.data.split('-')[1] == 'cancel')
    dp.register_callback_query_handler(sub_renewal_verification, lambda call: call.data.split('-')[1] == 'check')
    dp.register_callback_query_handler(sub_renewal_payment_inline, lambda call: call.data.split('-')[0] == 'renewal')