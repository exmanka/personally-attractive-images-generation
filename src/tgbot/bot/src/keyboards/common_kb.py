from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from src.services import localization as loc

welcome = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.common.btns['welcome_start'])).\
    add(KeyboardButton(loc.common.btns['welcome_about_project']))

sex = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.common.btns['welcome_sex_male'])).insert(KeyboardButton(loc.common.btns['welcome_sex_female'])).insert(KeyboardButton(loc.common.btns['welcome_sex_other'])).\
    add(KeyboardButton(loc.common.btns['welcome_cancel']))

model = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.common.btns['model_stylegan'])).insert(KeyboardButton(loc.common.btns['model_dcgan'])).\
    add(KeyboardButton(loc.common.btns['welcome_cancel']))