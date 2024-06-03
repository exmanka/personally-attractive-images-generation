from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.services import localization as loc


menu = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.admin.btns['send_message'])).insert(KeyboardButton(loc.admin.btns['about_clients'])).insert(KeyboardButton(loc.admin.btns['show_earnings'])).\
    add(KeyboardButton(loc.admin.btns['promo'])).insert(KeyboardButton(loc.admin.btns['subscriptions'])).\
    add(KeyboardButton(loc.admin.btns['reset_fsm_1']))

notification = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.admin.btns['send_message_everyone'])).insert(KeyboardButton(loc.admin.btns['send_message_selected'])).\
    add(KeyboardButton(loc.admin.btns['reset_fsm_2']))