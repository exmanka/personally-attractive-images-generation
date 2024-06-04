import asyncio
import logging
import datetime
import numpy as np
from io import BytesIO
from babel import dates
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import Message, MediaGroup, ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound, WrongFileIdentifier
from src.database import postgres
from src.services import api, localization as loc
from bot_init import bot, ADMIN_ID, LOCALIZATION_LANGUAGE


logger = logging.getLogger(__name__)


async def get_generated_image(model: str,
                              seed: np.ndarray,
                              resize_ratio: int = 2) -> Image.Image:
    """Get generated image by API according to model by specified seed.

    :param model: 'stylegan' | 'dcgan'
    :param seed: seed to be passed to generator using API
    :param resize_ration: div resize ration, defaults to 2
    """
    seed_bytes = seed.tobytes()
    seed_file = {'seed': seed_bytes}

    match model:
        case 'dcgan':
            pass
        case 'stylegan3':
            status_code, data = await api.post('http://stylegan-generator:8000/generate/', seed_file, __name__)
    
    if status_code == 200:
        image = Image.open(BytesIO(data))
        image = image.resize((image.width // resize_ratio, image.height // resize_ratio))
    else:
        image = Image.new('RGB', (512, 512), 'white')
    
    return image


async def draw_image_number(image: Image.Image,
                            number: int,
                            text_size: int = 16,
                            font_size: int = 48,
                            text_fill: tuple = (255, 255, 255)) -> Image.Image:
    """Draw number on picture.

    :param image: image where draw
    :param number: number to draw
    :param text_size: size of the text, defaults to 16
    :param font_size: size of the font, defaults to 48
    :param text_fill: color of the text, defaults to (255, 255, 255)
    """
    draw = ImageDraw.Draw(image)
    draw.text((text_size, text_size), str(number), fill=text_fill, font=ImageFont.load_default(font_size))

    return image


async def create_general_image(images_list: list[Image.Image],
                               image_rows: int = 4,
                               image_cols: int = 3,
                               spacing_size: int = 10,
                               border_size: int = 2) -> BytesIO:
    """Create general image from specified list of images."""    
    image_width_max = max(img.width for img in images_list)
    image_height_max = max(img.height for img in images_list)
    final_image_width = (image_width_max + spacing_size) * image_cols
    final_image_height = (image_height_max + spacing_size) * image_rows
    final_image = Image.new('RGB', (final_image_width, final_image_height), 'white')

    x_offset = border_size
    y_offset = border_size
    counter = 0
    for img in images_list:
        final_image.paste(img, (x_offset, y_offset))
        x_offset += img.width + spacing_size
        counter += 1
        if counter % image_cols == 0:
            x_offset = border_size
            y_offset += img.height + spacing_size

    final_image_bytes = BytesIO()
    final_image.save(final_image_bytes, format='PNG')
    final_image_bytes.seek(0)

    return final_image_bytes


async def convert_datetime(datatime_to_convert: datetime.datetime | None,
                           template: str = "d MMMM yyyy 'в' HH:mm") -> str:
    """Convert datatime.datetime object to string using template in CLDR format. If specified object is None, return 'None'.

    :param datatime_to_convert:
    :param template: template in CLDR format, defaults to "d MMMM yyyy 'в' HH:mm"
    :return: datatime in string format or 'None' if specified object is None
    :rtype: str
    """
    if datatime_to_convert:
        return dates.format_datetime(datatime_to_convert, format=template, locale=LOCALIZATION_LANGUAGE)
    
    return 'None'


async def format_none_string(string: str | None, prefix: str = ' ', postfix: str = '') -> str:
    """Return empty string '' if specified object is None, else return specified string with prefix and postfix.
    
    Use for fast object conversion before str.format method usage.

    :param string: object that needs to be formatted
    :param prefix: prefix added to specified string if it's not None, defaults to ' '
    :param postfix: prefix added to specified string if it's not None, defaults to ''
    :return: empty string or prefix + string + postfix
    """    
    return '' if string is None else prefix + string + postfix


async def send_message_by_telegram_id(telegram_id: int, message: Message):
    """Send specified message by provided telegram_id.

    :param telegram_id:
    :param message:
    :raises Exception: unrecognized message type
    """
    # if message is text
    if text := message.text:
        await bot.send_message(telegram_id, text, parse_mode='HTML')

    # if message is animation (GIF or H.264/MPEG-4 AVC video without sound)
    elif animation := message.animation:
        await bot.send_animation(telegram_id, animation.file_id)

    # if message is audio (audio file to be treated as music)
    elif audio := message.audio:
        await bot.send_audio(telegram_id, audio.file_id, caption=message.caption, parse_mode='HTML')

    # if message is document
    elif document := message.document:
        await bot.send_document(telegram_id, document.file_id, caption=message.caption, parse_mode='HTML')

    # if message is photo
    elif photo := message.photo:
        await bot.send_photo(telegram_id, photo[0].file_id, caption=message.caption, parse_mode='HTML')

    # if message is sticker
    elif sticker := message.sticker:
        await bot.send_sticker(telegram_id, sticker.file_id)

    # if message is video
    elif video := message.video:
        await bot.send_video(telegram_id, video.file_id, caption=message.caption, parse_mode='HTML')

    # if message is video note
    elif video_note := message.video_note:
        await bot.send_video_note(telegram_id, video_note.file_id)

    # if message is voice
    elif voice := message.voice:
        await bot.send_voice(telegram_id, voice.file_id, caption=message.caption, parse_mode='HTML')

    # other cases
    else:
        raise Exception('unrecognized message type')


async def autocheck_payment_status(payment_id: int) -> str:
    """Automatically check payment is successful according to YooMoney for 300 seconds.

    :param payment_id:
    :return: autochecker status, 'success' - payment was successfully finished, 'failure' - payment wasn't successfully finished in 300 seconds,
    'already_checked' - payment was already checked and added to db as successful by other functions
    """
    wallet = aiomoney.YooMoneyWallet(YOOMONEY_TOKEN)

    # Wait for user to redirect to Yoomoney site first 10 seconds
    await asyncio.sleep(10)

    # After that check Yoomoney payment status using linear equation
    k = 0.04
    b = 1
    for x in range(100):

        # If user has already checked successful payment and it was added to account subscription
        if await postgres.get_payment_status(payment_id):
            return 'already_checked'

        # If payment was successful according to YooMoney info
        if await wallet.check_payment_on_successful(payment_id):
            return 'success'

        await asyncio.sleep(k * x + b)

    return 'failure'


async def send_payment(telegram_id: int, chat_id: int, payment_menu_message_id: int, days_number: int):
    """Create message with subscription renewal payment link, run autochecker for payment and notify about successful payment."""
    # Get client_id by telegramID
    client_id = await postgres.get_clientID_by_telegramID(telegram_id)

    # Get client's sub info
    sub_id, sub_title, *_ = await postgres.get_subscription_info_by_clientID(client_id)
    payment_price = 2

    # Create entity in db table payments and get payment_id
    payment_id = await postgres.insert_payment(client_id, sub_id, payment_price, days_number)

    # Use aiomoney for payment link creation
    wallet = aiomoney.YooMoneyWallet(YOOMONEY_TOKEN)
    payment_form = await wallet.create_payment_form(
        amount_rub=payment_price,
        unique_label=payment_id,
        payment_source=aiomoney.PaymentSource.YOOMONEY_WALLET,
        success_redirect_url="https://github.com/exmanka/ltrinvestment-telegram-bot"
    )

    # Answer with InlineKeyboardMarkup with link to payment
    payment_msg = await bot.send_message(telegram_id, loc.internal.msgs['payment_form'].format(sub_title, days_number, payment_price, payment_id), 'HTML',
                                         reply_markup=await client_kb.sub_renewal_link_inline(payment_form.link_for_customer, payment_id, payment_price))

    # Delete payment menu message
    await bot.delete_message(chat_id, payment_menu_message_id)

    # Run payment autochecker for 310 seconds
    client_last_payment_status = await autocheck_payment_status(payment_id)

    # If autochecker returns successful payment info
    if client_last_payment_status == 'success':
        await postgres.update_payment_successful(payment_id, client_id, days_number)

        # Try to delete payment message
        try:
            await bot.delete_message(chat_id, payment_msg.message_id)

        # If already deleted
        except MessageToDeleteNotFound as _t:
            pass

        finally:
            await bot.send_message(telegram_id, loc.internal.msgs['payment_successful'].format(payment_id), reply_markup=client_kb.menu)


async def show_payment_menu_inline(telegram_id: int):
    """Show inline menu with subscription renewal price according to subscription type."""
    sub_id, *_ = await postgres.get_subscription_info_by_clientID(await postgres.get_clientID_by_telegramID(telegram_id))
    days_prices_list = await postgres.get_subscription_prices_info(sub_id)
    await bot.send_message(telegram_id, loc.client.msgs['renewal_info'], 'HTML',
                           reply_markup=await client_kb.sub_renewal_menu_inline(days_prices_list))
    

async def sub_renewal_verification(telegram_id: int, chat_id: int, message_id: int, payment_id: int, is_subscription_blank: bool):
    """Verify client's payment are successful according to YooMoney information."""
    wallet = aiomoney.YooMoneyWallet(YOOMONEY_TOKEN)
    client_id = await postgres.get_clientID_by_telegramID(telegram_id)

    # If payment wasn't added to db as successful and payment is successful according to Yoomoney:
    if await postgres.get_payment_status(payment_id) == False and await wallet.check_payment_on_successful(payment_id):

        # Update payment in db as successful
        days_number = await postgres.get_payment_days_number(payment_id)
        await postgres.update_payment_successful(payment_id, client_id, days_number)

        # Delete payment message
        await bot.delete_message(chat_id, message_id)

        # Answer to a client
        # If client paid blank subscription, go to client_kb.menu
        if is_subscription_blank:
            await bot.send_message(telegram_id, loc.internal.msgs['payment_found'].format(payment_id), parse_mode='HTML', reply_markup=client_kb.menu)

        # Else stay in the same keyboard menu
        else:
            await bot.send_message(telegram_id, loc.internal.msgs['payment_found'].format(payment_id), parse_mode='HTML')

    # If payment not found
    else:
        await bot.send_message(telegram_id, loc.internal.msgs['payment_not_found'].format(payment_id))
