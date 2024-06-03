import logging
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from src.keyboards import common_kb
from src.states import common_fsm
from src.database import postgres
from src.services import api, localization as loc


logger = logging.getLogger(__name__)


async def fsm_cancel(msg: Message, state: FSMContext):
    """Cancel FSM state and return to main menu."""
    await state.finish()
    await msg.answer(loc.common.msgs['return_to_main_menu'], parse_mode='HTML', reply_markup=common_kb.welcome)


async def welcome_fsm_start(msg: Message):
    """Start FSM for gathering user information."""
    await msg.answer(loc.common.msgs['welcome_sex'], parse_mode='HTML', reply_markup=common_kb.sex)
    await common_fsm.UserInfo.sex.set()


async def welcome_fsm_sex(msg: Message):
    """Gather sex (gender) information and add user to database."""
    database_enum = {loc.common.btns['welcome_sex_male']: 'male',
                     loc.common.btns['welcome_sex_female']: 'female',
                     loc.common.btns['welcome_sex_other']: 'other'}
    
    user = msg.from_user
    await postgres.insert_client(user.first_name, user.id, database_enum[msg.text], user.last_name, user.username)
    
    await msg.answer(loc.common.msgs['welcome_finish'], parse_mode='HTML')
    await msg.answer(loc.common.msgs['model_selection'], parse_mode='HTML', reply_markup=common_kb.model)
    await common_fsm.Model.selection.set()


async def generation_stylegan(msg: Message):
    """Test."""
    seed = np.random.rand(10, 10).astype(np.float32)
    seed_bytes = seed.tobytes()
    seed_file = {'seed': seed_bytes}

    IMAGES_NUMBER = 12
    IMAGES_ROWS = 4
    IMAGES_COLS = 3
    TEXT_SIZE = 16
    TEXT_FILL = (255, 255, 255)
    FONT = ImageFont.load_default()
    SPACING_SIZE = 10
    BORDER_SIZE = SPACING_SIZE // 4
    FONT = ImageFont.load_default(48)
        

    images_list: list[Image.Image] = []
    for i in range(IMAGES_NUMBER):
        status_code, data = await api.post('http://stylegan-generator:8000/generate/', seed_file, __name__)
        if status_code == 200:
            image = Image.open(BytesIO(data))
            image = image.resize((image.width // 2, image.height // 2))
            draw = ImageDraw.Draw(image)
            text = str(i + 1)
            draw.text((TEXT_SIZE, TEXT_SIZE), text, fill=TEXT_FILL, font=FONT)
            images_list.append(image)
        else:
            await msg.answer(loc.common.msgs['model_generation_error'].format(status_code))

    image_width_max = max(img.width for img in images_list)
    image_height_max = max(img.height for img in images_list)
    final_image_width = (image_width_max + SPACING_SIZE) * IMAGES_COLS
    final_height_width = (image_height_max + SPACING_SIZE) * IMAGES_ROWS
    final_image = Image.new('RGB', (final_image_width, final_height_width), 'white')

    x_offset = BORDER_SIZE
    y_offset = BORDER_SIZE
    counter = 0
    for img in images_list:
        final_image.paste(img, (x_offset, y_offset))
        x_offset += img.width + SPACING_SIZE
        counter += 1
        if counter % IMAGES_COLS == 0:
            x_offset = BORDER_SIZE
            y_offset += img.height + SPACING_SIZE

    final_image_bytes = BytesIO()
    final_image.save(final_image_bytes, format='PNG')
    final_image_bytes.seek(0)
    await msg.answer_photo(final_image_bytes)


# async def generation_stylegan(msg: Message):
#     """Test."""
#     seed = np.random.rand(10, 10).astype(np.float32)
#     seed_bytes = seed.tobytes()

#     seed_file = {'seed': seed_bytes}

#     status_code, data = await api.post('http://stylegan-generator:8000/generator/', seed_file, __name__)

#     # If HTTP status is 200 (OK)
#     if status_code == 200:
#         image_bytes = BytesIO(data)
#         image_bytes.seek(0)
#         await msg.answer_photo(image_bytes)

#     # If got another HTTP status
#     else:
#         await msg.answer(f'Ошибка: {status_code}')


async def command_restart(msg: Message, state: FSMContext = None):
    """Restart bot and send message when /restart command is pressed."""
    await msg.answer(loc.common.msgs['restart'], 'HTML', reply_markup=common_kb.welcome)
    await state.finish()


async def command_help(msg: Message):
    """Send message with information about provided help."""
    await msg.answer(loc.common.msgs['help'], 'HTML')


async def command_start(msg: Message):
    """Send message when /start command is pressed."""
    await msg.answer(loc.common.msgs['start'], 'HTML', reply_markup=common_kb.welcome)


async def unrecognized_messages(msg: Message):
    """Answer unrecognized messages."""
    await msg.answer(loc.common.msgs['unrecognized'], 'HTML')


def register_handlers(dp: Dispatcher):
    """Register shared handlers in dispatcher."""
    dp.register_message_handler(fsm_cancel, Text(loc.common.btns['welcome_cancel'], ignore_case=True), state=[None, common_fsm.Model.selection])
    dp.register_message_handler(welcome_fsm_start, Text(loc.common.btns['welcome_model_selection'], ignore_case=True))
    dp.register_message_handler(generation_stylegan, commands=['test'], state='*')
    dp.register_message_handler(command_restart, commands=['restart'], state='*')
    dp.register_message_handler(command_start, commands=['start'], state='*')
    dp.register_message_handler(command_help, commands=['help'], state='*')
    dp.register_message_handler(unrecognized_messages, state="*")
