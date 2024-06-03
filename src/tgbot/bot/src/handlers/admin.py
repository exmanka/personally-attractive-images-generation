import logging
from decimal import Decimal
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import ChatNotFound, BotBlocked
from src.middlewares import admin_mw
from src.keyboards import admin_kb
from src.states import admin_fsm
from src.database import postgres
from src.services import internal, localization as loc


logger = logging.getLogger(__name__)


@admin_mw.admin_only()
async def fsm_reset(msg: Message, state: FSMContext):
    """Cancel admin's FSM state and return to menu keyboard regardless of machine state."""
    await state.finish()
    await msg.answer(loc.admin.msgs['reset_fsm_keyboard'], parse_mode='HTML', reply_markup=admin_kb.menu)


@admin_mw.admin_only()
async def show_admin_keyboard(msg: Message):
    """Send message with information about admin's commands and show admin keyboard."""
    await msg.reply(loc.admin.msgs['admin_kb_info'], parse_mode='HTML', reply_markup=admin_kb.menu)


@admin_mw.admin_only()
async def notifications_menu(msg: Message):
    """Show keyboard for sending messages via bot."""
    await msg.answer(loc.admin.msgs['go_send_message_menu'], parse_mode='HTML', reply_markup=admin_kb.notification)


@admin_mw.admin_only()
async def notifications_send_message_everyone_fsm_start(message: Message, state: FSMContext):
    """Start FSM for sending message to every client who wrote bot at least one time."""
    await state.set_state(admin_fsm.SendMessage.everyone)
    await message.answer(loc.admin.msgs['message_everyone_info'])


@admin_mw.admin_only()
async def notifications_send_message_everyone(message: Message, state: FSMContext):
    """Catch message, echo message and send it to every client who wrote bot at least one time, if admin wrote /perfect."""
    # If message looks good for admin
    if message.text and message.text == '/perfect':
        ignored_clients_str = ''
        async with state.proxy() as data:

            # For every client
            for idx, [telegram_id] in enumerate(await postgres.get_clients_telegram_ids()):
                try:
                    await internal.send_message_by_telegram_id(telegram_id, data['message'])

                # Add him to message list of clients who didn't receive message
                except ChatNotFound as _t:
                    # Add him to message list of clients who didn't receive message
                    _, name, surname, username, *_ = await postgres.get_client_info_by_telegramID(telegram_id)
                    ignored_clients_str += loc.admin.msgs['clients_row_str'].format(idx + 1, name, surname, username, telegram_id)

                # If client blocked bot
                except BotBlocked as bb:
                    # Add him to message list of clients who didn't receive message and add info to log
                    _, name, surname, username, *_ = await postgres.get_client_info_by_telegramID(telegram_id)
                    logger.info(f"Can't send message to client {name} {telegram_id}: {bb}")
                    ignored_clients_str += loc.admin.msgs['clients_row_str'].format(idx + 1, name, surname, username, telegram_id) + '(has blocked bot)\n'

        # If some clients didn't receive message because they didn't write to bot at all
        if ignored_clients_str:
            answer_message = loc.admin.msgs['message_everyone_was_sent'] + '\n\n' + loc.admin.msgs['message_everyone_somebody_didnt_recieve']\
                .format(ignored_clients_str=ignored_clients_str)
            await message.answer(answer_message, parse_mode='HTML')

        # If all clients receive message
        else:
            await message.answer(loc.admin.msgs['message_everyone_was_sent'] + '\n\n' + loc.admin.msgs['message_everyone_everybody_received'], parse_mode='HTML')

        await fsm_reset(message, state)
        return

    await message.answer(loc.admin.msgs['how_message_looks'])

    # Echo message showing how will be displayed admin's message for clients
    await internal.send_message_by_telegram_id(message.from_user.id, message)

    # Save last message to send it if admin write /perfect
    async with state.proxy() as data:
        data['message'] = message


@admin_mw.admin_only()
async def notifications_send_message_selected_fsm_start(message: Message, state: FSMContext):
    """Start FSM for sending message to selected clients."""
    await state.set_state(admin_fsm.SendMessage.selected_list)
    await message.answer(loc.admin.msgs['message_selected_info'], parse_mode='HTML')


@admin_mw.admin_only()
async def notifications_send_message_selected_list(message: Message, state: FSMContext):
    """Parse entered by admin list of selected clients for sending them some message."""
    # Parse clients mentioned in message
    selected_clients = message.text.split(' ')
    selected_clients_telegram_ids = []
    for client in selected_clients:

        # If client mentioned by username
        if client[0] == '@':

            # If client exists in db
            if telegram_id := await postgres.get_telegramID_by_username(client):
                selected_clients_telegram_ids.append(telegram_id)

        # If client mentioned by telegram_id and exists in db
        elif await postgres.get_clientID_by_telegramID(int(client)):
            selected_clients_telegram_ids.append(int(client))

    # Save selected clients ids
    async with state.proxy() as data:
        data['selected_telegram_ids'] = selected_clients_telegram_ids
    await state.set_state(admin_fsm.SendMessage.selected)

    # Show selected clients info
    selected_clients_str = ''
    for idx, telegram_id in enumerate(selected_clients_telegram_ids):
        _, name, surname, username, *_ = await postgres.get_client_info_by_telegramID(telegram_id)
        selected_clients_str += loc.admin.msgs['clients_row_str'].format(idx + 1, name, surname, username, telegram_id)

    # If at least 1 selected client exists in db
    if selected_clients_str:
        await message.answer(loc.admin.msgs['message_selected_somebody_received'].format(selected_clients_str=selected_clients_str), parse_mode='HTML')
        await message.answer(loc.admin.msgs['message_selected_enter_message_info'])

    # if mentioned clients don't exist in db
    else:
        await message.answer(loc.admin.msgs['message_selected_nobody_received'], parse_mode='HTML')


@admin_mw.admin_only()
async def notifications_send_message_selected(message: Message, state: FSMContext):
    """Catch message, echo message and send it to selected clients, if admin wrote /perfect."""
    # If message looks good for admin
    if message.text and message.text == '/perfect':
        ignored_clients_str = ''
        async with state.proxy() as data:

            # For every existing in db selected client
            for idx, telegram_id in enumerate(data['selected_telegram_ids']):
                try:
                    await internal.send_message_by_telegram_id(telegram_id, data['message'])

                # Add him to message list of clients who didn't receive message
                except ChatNotFound as _t:
                    # Add him to message list of clients who didn't receive message
                    _, name, surname, username, *_ = await postgres.get_client_info_by_telegramID(telegram_id)
                    ignored_clients_str += loc.admin.msgs['clients_row_str'].format(idx + 1, name, surname, username, telegram_id)

                # If client blocked bot
                except BotBlocked as bb:
                    # Add him to message list of clients who didn't receive message and add info to log
                    _, name, surname, username, *_ = await postgres.get_client_info_by_telegramID(telegram_id)
                    logger.info(f"Can't send message to client {name} {telegram_id}: {bb}")
                    ignored_clients_str += loc.admin.msgs['clients_row_str'].format(idx + 1, name, surname, username, telegram_id) + '(has blocked bot)\n'

        # If some clients didn't receive message because they didn't write to bot at all
        if ignored_clients_str:
            answer_message = loc.admin.msgs['message_everyone_was_sent'] + '\n\n' + loc.admin.msgs['message_everyone_somebody_didnt_recieve']\
                .format(ignored_clients_str=ignored_clients_str)
            await message.answer(answer_message, parse_mode='HTML')

        # If all clients receive message
        else:
            await message.answer(loc.admin.msgs['message_everyone_was_sent'] + '\n\n' + loc.admin.msgs['message_everyone_everybody_received'], parse_mode='HTML')
    
        await fsm_reset(message, state)
        return

    await message.answer(loc.admin.msgs['how_message_looks'])

    # Echo message showing how will be displayed admin's message for clients
    await internal.send_message_by_telegram_id(message.from_user.id, message)

    # Save last message to send it if admin write /perfect
    async with state.proxy() as data:
        data['message'] = message


@admin_mw.admin_only()
async def show_clients_info(msg: Message):
    """Send message with information about all clients. Add /clients [-h] flag to get human-readable message."""
    # Check command /clients is called with -h flag
    is_human_readable = False
    command_flags: list = msg.text.split(' ')
    if len(command_flags) > 1 and command_flags[1] == '-h':
        is_human_readable = True

    answer_message = ''
    for [client_id] in await postgres.get_clients_ids():
        name, surname, username, telegram_id, register_date = await postgres.get_client_info_by_clientID(client_id)
        register_date_converted = await internal.convert_datetime(register_date, 'd MMMM yyyy')
        sub_id, *_ = await postgres.get_subscription_info_by_clientID(client_id)
        _, sub_price = await postgres.get_subscription_prices_main_info(sub_id)
        sub_expiration_date = await postgres.get_subscription_expiration_date(telegram_id)
        sub_expiration_date_converted = await internal.convert_datetime(sub_expiration_date)
        paid_sum: Decimal = await postgres.get_payments_successful_sum(client_id)

        answer_message_row = ''
        if await postgres.is_subscription_active(telegram_id):
            answer_message_row += loc.admin.msgs['about_clients_sub_active']
        else:
            answer_message_row += loc.admin.msgs['about_clients_sub_inactive']

        # Hope that telegram add ability to send markdown's spreadsheets in message to api, but for now
        answer_message_row +=\
            f"| <b>{client_id}</b> "\
            f"|{await internal.format_none_string(username)} <code>{name}{await internal.format_none_string(surname)}</code> <code>{telegram_id}</code>, {register_date_converted} "\
            f"| {sub_price}₽/мес, <b>{sub_expiration_date_converted}</b> "\
            f"| paid: {float(paid_sum):g}₽ "

        answer_message += answer_message_row + '\n' + '\n' * int(is_human_readable)

        # If human readable format: send message for every 10 client_id to avoid telegram message length restrictions
        if is_human_readable and client_id % 10 == 0:
            await msg.answer(answer_message, parse_mode='HTML')
            answer_message = ''

        # If standard format: send message for every 25 client_id to avoid telegram message length restrictions
        elif not is_human_readable and client_id % 25 == 0:
            await msg.answer(f"<pre>{answer_message}</pre>", parse_mode='HTML')
            answer_message = ''
    
    # Send remaining info
    if answer_message and is_human_readable:
        await msg.answer(answer_message, parse_mode='HTML')
    elif answer_message and not is_human_readable:
        await msg.answer(f"<pre>{answer_message}</pre>", 'HTML')


@admin_mw.admin_only()
async def show_earnings(msg: Message):
    """Send message with information about earned money per current month."""
    earnings_per_current_month: Decimal = await postgres.get_earnings_per_month()
    await msg.answer(loc.admin.msgs['show_earnings'].format(float(earnings_per_current_month)), parse_mode='HTML')


def register_handlers(dp: Dispatcher):
    """Register admin handlers in dispatcher."""
    dp.register_message_handler(fsm_reset, Text([loc.admin.btns[key] for key in ('reset_fsm_1', 'reset_fsm_2')]), state='*')
    dp.register_message_handler(fsm_reset, commands=['reset'], state='*')
    dp.register_message_handler(show_admin_keyboard, commands=['admin'], state='*')
    dp.register_message_handler(notifications_menu, Text(loc.admin.btns['send_message']))
    dp.register_message_handler(notifications_send_message_everyone_fsm_start, Text(loc.admin.btns['send_message_everyone']))
    dp.register_message_handler(notifications_send_message_everyone, state=admin_fsm.SendMessage.everyone, content_types='any')
    dp.register_message_handler(notifications_send_message_selected_fsm_start, Text(loc.admin.btns['send_message_selected']))
    dp.register_message_handler(notifications_send_message_selected_list, state=admin_fsm.SendMessage.selected_list)
    dp.register_message_handler(notifications_send_message_selected, state=admin_fsm.SendMessage.selected, content_types='any')
    dp.register_message_handler(show_clients_info, Text(loc.admin.btns['about_clients']))
    dp.register_message_handler(show_clients_info, commands=['clients'])
    dp.register_message_handler(show_earnings, Text(loc.admin.btns['show_earnings']))
