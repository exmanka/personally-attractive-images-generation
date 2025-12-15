import logging
import numpy as np
import re
from io import BytesIO
from aiogram import Dispatcher
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from src.keyboards import common_kb
from src.states import common_fsm
from src.database import postgres
from src.services import internal, localization as loc
from bot_init import bot, IMAGES_ROWS, IMAGES_COLS, IMAGES_NUMBER, SCORE_BASIC, STAGES_NUMBER


logger = logging.getLogger(__name__)


async def fsm_cancel(msg: Message, state: FSMContext):
    """Cancel FSM state and return to main menu."""
    await state.finish()
    await msg.answer(loc.common.msgs['return_to_main_menu'], parse_mode='HTML', reply_markup=common_kb.welcome)


async def welcome_fsm_start(msg: Message, state: FSMContext):
    """Start FSM for gathering user information if client is not registered."""
    if await postgres.is_user_registered(msg.from_user.id):
        await state.set_state(common_fsm.Model.selection)
        await msg.answer(loc.common.msgs['model_selection'], parse_mode='HTML', reply_markup=common_kb.model)
    else:
        await state.set_state(common_fsm.UserInfo.sex)
        await msg.answer(loc.common.msgs['welcome_gather_info'], parse_mode='HTML')
        await msg.answer(loc.common.msgs['welcome_sex'], parse_mode='HTML', reply_markup=common_kb.sex)


async def welcome_fsm_sex(msg: Message, state: FSMContext):
    """Gather sex (gender) information and add user to database."""
    database_enum = {loc.common.btns['welcome_sex_male']: 'male',
                     loc.common.btns['welcome_sex_female']: 'female',
                     loc.common.btns['welcome_sex_other']: 'other'}
    user = msg.from_user
    await postgres.insert_user(user.first_name, user.id, database_enum[msg.text], user.last_name, user.username)
    
    await state.set_state(common_fsm.Model.selection)
    await msg.answer(loc.common.msgs['welcome_finish'], parse_mode='HTML')
    await msg.answer(loc.common.msgs['model_selection'], parse_mode='HTML', reply_markup=common_kb.model)


async def generation_fsm_cancel(msg: Message, state: FSMContext):
    """Cancel FSM state for generation and return to model menu."""
    await state.finish()
    await state.set_state(common_fsm.Model.selection)
    await msg.answer(loc.common.msgs['model_cancel'], parse_mode='HTML', reply_markup=common_kb.model)


async def generation_fsm_start(msg: Message, state: FSMContext):
    """Start FSM for images generation and generate images for the first step."""
    if msg.text == loc.common.btns['model_dcgan']:
        await msg.answer('👾 <b>К сожалению, модель DCGAN пока что недоступна в виду аппаратных ограничений!</b>', parse_mode='HTML')
        return
    await state.set_state(common_fsm.Model.generation_in_process)

    async with state.proxy() as data:
        data['stage'] = 1
        await msg.answer(loc.common.msgs['model_generation_process'].format(data['stage'], STAGES_NUMBER), parse_mode='HTML', reply_markup=common_kb.generation)
    
    await bot.send_chat_action(msg.from_user.id, 'typing')

    database_enum = {loc.common.btns['model_dcgan']: 'dcgan',
                     loc.common.btns['model_stylegan']: 'stylegan3'}
    model_str = database_enum[msg.text]
    
    seed_size_dict = {loc.common.btns['model_dcgan']: 100,
                      loc.common.btns['model_stylegan']: 512}
    seed_size = seed_size_dict[msg.text]

    seeds_list = [(np.float32(np.random.normal(size=seed_size))).tolist() for _ in range(IMAGES_NUMBER)]
    images_list = []
    for idx, seed in enumerate(seeds_list):
        image = await internal.get_generated_image(model_str, np.array(seed, dtype=np.float32))
        image = await internal.draw_image_number(image, idx + 1)
        images_list.append(image)

    async with state.proxy() as data:
        data['seed_size'] = seed_size
        data['seeds_list'] = seeds_list
        data['images_list'] = images_list
        data['model_str'] = model_str
        data['attractive_list'] = []
        data['unattractive_list'] = []

    final_image = await internal.create_general_image(images_list, IMAGES_ROWS, IMAGES_COLS)
    
    await state.set_state(common_fsm.Model.generation_feedback_attractive)
    await msg.answer_photo(final_image)
    await msg.answer(loc.common.msgs['model_generation_feedback_attractive'], parse_mode='HTML', reply_markup=ReplyKeyboardRemove())


async def generation_feedback_attractive(msg: Message, state: FSMContext):
    """Get and save feedback for attractive image."""
    if re.fullmatch(re.compile(r"^([1-9]|10|11|12)\s([1-9]|10)$"), msg.text):
        await state.set_state(common_fsm.Model.generation_feedback_unattractive)
        image_number, image_score = map(int, msg.text.split(' '))

        async with state.proxy() as data:
            data['attractive_list'].append([data['images_list'][image_number - 1], data['seeds_list'][image_number - 1], image_score])

        await msg.answer(loc.common.msgs['model_generation_feedback_unattractive'], parse_mode='HTML')
    else:
        await msg.answer(loc.common.msgs['model_generation_feedback_incorrect_input'], parse_mode='HTML')


async def generation_feedback_unattractive(msg: Message, state: FSMContext):
    """Get and save feedback for unattractive image."""
    if re.fullmatch(re.compile(r"^([1-9]|10|11|12)\s([1-9]|10)$"), msg.text):
        await state.set_state(common_fsm.Model.generation_generate)
        image_number, image_score = map(int, msg.text.split(' '))
        
        async with state.proxy() as data:
            data['unattractive_list'].append([data['images_list'][image_number - 1], data['seeds_list'][image_number - 1], image_score])

        await generation_generate(msg, state)
    else:
        await msg.answer(loc.common.msgs['model_generation_feedback_incorrect_input'], parse_mode='HTML')


async def generation_generate(msg: Message, state: FSMContext):
    """Generate images using NVIDIA StyleGAN 3 for all steps except the first one."""
    async with state.proxy() as data:
        data['stage'] += 1

        if data['stage'] > STAGES_NUMBER:
            await msg.answer(loc.common.msgs['model_generation_end'], parse_mode='HTML')

            first_image_bytes = BytesIO()
            data['attractive_list'][0][0].save(first_image_bytes, format='PNG')
            first_image_bytes.seek(0)
            await msg.answer_photo(first_image_bytes, caption=loc.common.msgs['model_generation_end_score_first'].format(data['attractive_list'][0][2]), parse_mode='HTML')

            second_image_bytes = BytesIO()
            data['attractive_list'][1][0].save(second_image_bytes, format='PNG')
            second_image_bytes.seek(0)
            await msg.answer_photo(second_image_bytes, caption=loc.common.msgs['model_generation_end_score_second'].format(data['attractive_list'][1][2]), parse_mode='HTML')

            last_image_bytes = BytesIO()
            data['attractive_list'][STAGES_NUMBER - 1][0].save(last_image_bytes, format='PNG')
            last_image_bytes.seek(0)
            await msg.answer_photo(last_image_bytes, caption=loc.common.msgs['model_generation_end_score_last'].format(data['attractive_list'][STAGES_NUMBER - 1][2]), parse_mode='HTML')

            await state.finish()
            await state.set_state(common_fsm.Model.selection)
            await msg.answer(loc.common.msgs['model_generation_thanks'], parse_mode='HTML', reply_markup=common_kb.model)

            return
    
    await state.set_state(common_fsm.Model.generation_in_process)

    async with state.proxy() as data:
        await msg.answer(loc.common.msgs['model_generation_process'].format(data['stage'], STAGES_NUMBER), parse_mode='HTML', reply_markup=common_kb.generation)
    
    await bot.send_chat_action(msg.from_user.id, 'typing')

    async with state.proxy() as data:
        if data['stage'] == 2:
            seeds_list = [(np.float32(np.random.normal(size=data['seed_size']))).tolist() for _ in range(IMAGES_NUMBER)]

        else:
            best_seed = np.zeros(data['seed_size'], dtype=np.float32)
            score_sum = 0
            for [_, seed, score] in data['attractive_list']:
                best_seed += np.array(seed, dtype=np.float32) * SCORE_BASIC ** score
                score_sum += SCORE_BASIC ** score
            best_seed /= score_sum

            seeds_list = []
            for i in range(IMAGES_ROWS - 1):
                for _ in range(IMAGES_COLS):
                    noise = np.float32(np.random.normal(scale=((i + 1) ** 2 * .1), size=data['seed_size']))
                    seeds_list.append((best_seed + noise).tolist())

            for _ in range(IMAGES_COLS):
                seeds_list.append((np.float32(np.random.normal(size=data['seed_size']))).tolist())

        images_list = []
        for idx, seed in enumerate(seeds_list):
            image = await internal.get_generated_image(data['model_str'], np.array(seed, dtype=np.float32))
            image = await internal.draw_image_number(image, idx + 1)
            images_list.append(image)

        data['seeds_list'] = seeds_list
        data['images_list'] = images_list

    final_image = await internal.create_general_image(images_list, IMAGES_ROWS, IMAGES_COLS)

    await state.set_state(common_fsm.Model.generation_feedback_attractive)
    await msg.answer_photo(final_image)
    await msg.answer(loc.common.msgs['model_generation_feedback_attractive'], parse_mode='HTML')


async def generation_in_process(msg: Message):
    """Send message with information that generation is in process."""
    await msg.answer(loc.common.msgs['model_generation_in_process'], 'HTML')


async def about_models(msg: Message):
    """Send message with information about models."""
    await msg.answer(loc.common.msgs['model_about'], 'HTML')


async def about_project(msg: Message):
    """Send message with information about project."""
    await msg.answer(loc.common.msgs['about_project'], 'HTML')


async def command_restart(msg: Message, state: FSMContext):
    """Restart bot and send message when /restart command is pressed."""
    await state.finish()
    await msg.answer(loc.common.msgs['restart'], 'HTML', reply_markup=common_kb.welcome)


async def command_help(msg: Message):
    """Send message with information about provided help."""
    await msg.answer(loc.common.msgs['help'], 'HTML')


async def command_start(msg: Message, state: FSMContext):
    """Send message when /start command is pressed."""
    await state.finish()
    await msg.answer(loc.common.msgs['start'], 'HTML', reply_markup=common_kb.welcome)


async def unrecognized_messages(msg: Message):
    """Answer unrecognized messages."""
    await msg.answer(loc.common.msgs['unrecognized'], 'HTML')


def register_handlers(dp: Dispatcher):
    """Register shared handlers in dispatcher."""
    dp.register_message_handler(fsm_cancel, Text(loc.common.btns['welcome_cancel']), state=[None, common_fsm.UserInfo.sex,
                                                                                            common_fsm.Model.selection])
    dp.register_message_handler(welcome_fsm_start, Text(loc.common.btns['welcome_start']))
    dp.register_message_handler(welcome_fsm_sex, Text([loc.common.btns[key] for key in ('welcome_sex_male',
                                                                                        'welcome_sex_female',
                                                                                        'welcome_sex_other')]),
                                                                                        state=common_fsm.UserInfo.sex)
    dp.register_message_handler(about_models, Text(loc.common.btns['model_about']), state=[None,
                                                                                           common_fsm.Model.selection])
    dp.register_message_handler(about_project, Text(loc.common.btns['welcome_about_project']), state=None)
    dp.register_message_handler(generation_fsm_cancel, Text(loc.common.btns['model_cancel']), state=[None,
                                                                                                     common_fsm.Model.generation_feedback_attractive,
                                                                                                     common_fsm.Model.generation_feedback_unattractive,
                                                                                                     common_fsm.Model.generation_generate,
                                                                                                     common_fsm.Model.generation_in_process])
    dp.register_message_handler(generation_fsm_start, Text([loc.common.btns[key] for key in ('model_dcgan',
                                                                                             'model_stylegan')]),
                                                                                             state=[None, common_fsm.Model.selection])
    dp.register_message_handler(command_restart, commands=['restart'], state='*')
    dp.register_message_handler(command_start, commands=['start'], state='*')
    dp.register_message_handler(command_help, commands=['help'], state='*')
    dp.register_message_handler(generation_feedback_attractive, state=common_fsm.Model.generation_feedback_attractive)
    dp.register_message_handler(generation_feedback_unattractive, state=common_fsm.Model.generation_feedback_unattractive)
    dp.register_message_handler(generation_in_process, state=common_fsm.Model.generation_in_process)
    dp.register_message_handler(unrecognized_messages, state="*")
