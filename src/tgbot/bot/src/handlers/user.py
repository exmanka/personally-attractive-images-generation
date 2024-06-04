from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from src.middlewares import user_mw
from src.keyboards import user_kb
from src.states import user_fsm
from src.database import postgres
from src.services import internal, localization as loc


async def welcome_return_menu(msg: Message, state: FSMContext):
    """Send message and return to welcome menu."""
    await state.finish()
    await msg.answer(loc.user.msgs['welcome_return'], 'HTML', reply_markup=user_kb.welcome)


async def welcome_examples(msg: Message):
    """Send message with examples of benefits from product."""
    await msg.answer(loc.user.msgs['welcome_examples'], 'HTML')


async def welcome_agreement(msg: Message):
    """Send message with information about user agreement."""
    await msg.answer(loc.user.msgs['welcome_agreement'], 'HTML')


async def welcome_manual(msg: Message):
    """Send message with information about manual to use service."""
    await msg.answer(loc.user.msgs['welcome_manual'], 'HTML')


async def welcome_about_project(msg: Message):
    """Send message with information about project."""
    await msg.answer(loc.user.msgs['welcome_about_project'], 'HTML')


async def welcome_subscribe(msg: Message):
    """Send message with inline payments links."""
    # If client (completed phone verification)
    if await postgres.is_user_registered(msg.from_user.id):

        # If client has blank subscription (never paid for it or never renewed it)
        if await postgres.is_subscription_blank(msg.from_user.id):
            await internal.show_payment_menu_inline(msg.from_user.id)

        # If client has already initiated subscription
        else:
            await msg.answer(loc.client.msgs['already_init_sub'])

    # If user (without phone verification)
    else:
        await user_fsm.PhoneVerification.ready.set()
        await msg.answer(loc.user.msgs['verify_number'], 'HTML', reply_markup=user_kb.phone_verification)


@user_mw.users_only()
async def welcome_phone_verification(msg: Message, state: FSMContext):
    """Verify user's phone number and send message with information about verification."""
    # If user send his own number
    if msg.contact.user_id == msg.from_user.id:
        await state.finish()

        # Insert user into database
        user = msg.from_user
        await postgres.insert_user(user.first_name, user.id, msg.contact.phone_number, user.last_name, user.username)
        
        # Notify client that phone verification is completed and return to user keyboard
        await msg.answer(loc.user.msgs['verify_number_ok'], 'HTML', reply_markup=user_kb.welcome)

        # Show inline payment menu
        await internal.show_payment_menu_inline(msg.from_user.id)

    # If user send someone else's contact
    else:
        await msg.answer(loc.user.msgs['verify_number_wrong'], 'HTML')


def register_handlers(dp: Dispatcher):
    """Register user handlers in dispatcher."""
    dp.register_message_handler(welcome_return_menu, Text(loc.user.btns['welcome_return']), state=[None,
                                                                                                   user_fsm.PhoneVerification.ready])
    dp.register_message_handler(welcome_subscribe, Text(loc.user.btns['welcome_subscribe']))
    dp.register_message_handler(welcome_examples, Text(loc.user.btns['welcome_examples']))
    dp.register_message_handler(welcome_agreement, Text(loc.user.btns['welcome_agreement']))
    dp.register_message_handler(welcome_manual, Text(loc.user.btns['welcome_manual']))
    dp.register_message_handler(welcome_about_project, Text(loc.user.btns['welcome_about_project']))
    dp.register_message_handler(welcome_phone_verification, state=user_fsm.PhoneVerification.ready, content_types='contact')