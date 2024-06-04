import logging
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from aiogram import Dispatcher
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from src.keyboards import common_kb
from src.states import common_fsm
from src.database import postgres
from src.services import api, internal, localization as loc
from bot_init import bot


logger = logging.getLogger(__name__)


async def fsm_cancel(msg: Message, state: FSMContext):
    """Cancel FSM state and return to main menu."""
    await state.finish()
    await msg.answer(loc.common.msgs['return_to_main_menu'], parse_mode='HTML', reply_markup=common_kb.welcome)


async def welcome_fsm_start(msg: Message, state: FSMContext):
    """Start FSM for gathering user information if client is not registered."""
    if await postgres.is_user_registered(msg.from_user.id):
        # await common_fsm.Model.selection.set()
        await state.set_state(common_fsm.Model.selection)
        await msg.answer(loc.common.msgs['model_selection'], parse_mode='HTML', reply_markup=common_kb.model)
    else:
        # await common_fsm.UserInfo.sex.set()
        await state.set_state(common_fsm.UserInfo.sex)
        await msg.answer(loc.common.msgs['welcome_sex'], parse_mode='HTML', reply_markup=common_kb.sex)


async def welcome_fsm_sex(msg: Message, state: FSMContext):
    """Gather sex (gender) information and add user to database."""
    database_enum = {loc.common.btns['welcome_sex_male']: 'male',
                     loc.common.btns['welcome_sex_female']: 'female',
                     loc.common.btns['welcome_sex_other']: 'other'}
    user = msg.from_user
    await postgres.insert_user(user.first_name, user.id, database_enum[msg.text], user.last_name, user.username)
    
    await state.set_state(common_fsm.Model.selection)
    # await common_fsm.Model.selection.set()
    await msg.answer(loc.common.msgs['welcome_finish'], parse_mode='HTML')
    await msg.answer(loc.common.msgs['model_selection'], parse_mode='HTML', reply_markup=common_kb.model)


async def generation_fsm_cancel(msg: Message, state: FSMContext):
    """Cancel FSM state for generation and return to model menu."""
    await state.set_state(common_fsm.Model.selection)
    await msg.answer(loc.common.msgs['model_cancel'], parse_mode='HTML', reply_markup=common_kb.model)


async def generation_fsm_start(msg: Message, state: FSMContext):
    """Start FSM for images generation and generate images for the first step."""
    await msg.answer(loc.common.msgs['model_generation_process'], parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
    await bot.send_chat_action(msg.from_user.id, 'typing')

    IMAGES_NUMBER = 12
    database_enum = {loc.common.btns['model_dcgan']: 'dcgan',
                     loc.common.btns['model_stylegan']: 'stylegan3'}
    
    if msg.text == loc.common.btns['model_dcgan']:
        await state.set_state(common_fsm.Model.generation_dcgan)
        seed_size = 100
    elif msg.text == loc.common.btns['model_stylegan']:
        await state.set_state(common_fsm.Model.generation_stylegan)
        seed_size = 512
    else:
        pass

    seeds_list = [np.float32(np.random.normal(size=seed_size)) for _ in range(IMAGES_NUMBER)]
    images_list = []
    model_str = database_enum[msg.text]
    for idx, seed in enumerate(seeds_list):
        image = await internal.get_generated_image(model_str, seed)
        image = await internal.draw_image_number(image, idx + 1)
        images_list.append(image)

    async with state.proxy() as data:
        data['seeds_list'] = seeds_list
        data['images_list'] = images_list
        data['model_str'] = model_str
        data['iter'] = 1

    final_image = await internal.create_general_image(images_list)

    await msg.answer_photo(final_image)
    await msg.answer(loc.common.msgs['model_generation_info'], parse_mode='HTML', reply_markup=common_kb.generation)


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


async def about_models(msg: Message):
    """Send message with information about models."""
    await msg.answer(loc.common.msgs['model_about'], 'HTML')


async def about_project(msg: Message):
    """Send message with information about project."""
    await msg.answer(loc.common.msgs['about_project'], 'HTML')


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
    dp.register_message_handler(fsm_cancel, Text(loc.common.btns['welcome_cancel']), state=[None, common_fsm.UserInfo.sex, common_fsm.Model.selection])
    dp.register_message_handler(welcome_fsm_start, Text(loc.common.btns['welcome_start']))
    dp.register_message_handler(welcome_fsm_sex, Text([loc.common.btns[key] for key in ('welcome_sex_male', 'welcome_sex_female', 'welcome_sex_other')]), state=common_fsm.UserInfo.sex)
    dp.register_message_handler(about_models, Text(loc.common.btns['model_about']), state=[None, common_fsm.Model.selection])
    dp.register_message_handler(about_project, Text(loc.common.btns['welcome_about_project']), state=None)
    dp.register_message_handler(generation_fsm_cancel, Text(loc.common.btns['model_cancel']), state=[None, common_fsm.Model.generation_dcgan, common_fsm.Model.generation_stylegan])
    dp.register_message_handler(generation_fsm_start, Text([loc.common.btns[key] for key in ('model_dcgan', 'model_stylegan')]), state=[None, common_fsm.Model.selection])
    dp.register_message_handler(generation_stylegan, commands=['test'], state='*')
    dp.register_message_handler(command_restart, commands=['restart'], state='*')
    dp.register_message_handler(command_start, commands=['start'], state='*')
    dp.register_message_handler(command_help, commands=['help'], state='*')
    dp.register_message_handler(unrecognized_messages, state="*")
