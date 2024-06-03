from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.services import localization as loc


welcome = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.user.btns['welcome_subscribe'])).\
    add(KeyboardButton(loc.user.btns['welcome_examples'])).\
    add(KeyboardButton(loc.user.btns['welcome_agreement'])).insert(KeyboardButton(loc.user.btns['welcome_manual'])).insert(KeyboardButton(loc.user.btns['welcome_about_project']))

phone_verification = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.user.btns['phone_verification'], request_contact=True)).\
    add(KeyboardButton(loc.user.btns['welcome_return']))