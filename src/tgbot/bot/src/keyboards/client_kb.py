from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from src.services import localization as loc


async def sub_renewal_menu_inline(num_days_prices: list) -> InlineKeyboardMarkup:
    """Return dynamic inline keyboard with different months payment options."""
    keybard = InlineKeyboardMarkup()

    # Add to keyboard button with minimal days number and price,
    # without showing discount
    num_days_prices_sorted = sorted(num_days_prices)
    main_days_number, main_price = num_days_prices_sorted[0]
    keybard.add(InlineKeyboardButton(loc.client.btns['renewal_inline'].format(main_days_number, main_price),
                                     callback_data=f'renewal-{main_days_number}'))
    
    # Add to keyboard buttons with other days numbers and prices in ASC order
    # with showing discount relative to minimal days number and price
    for days_number, price in num_days_prices_sorted[1:]:
        discount = (1 - price / (main_price * days_number / main_days_number)) * 100
        keybard.add(InlineKeyboardButton(loc.client.btns['renewal_discount_inline'].format(days_number, price, discount),
                                         callback_data=f'renewal-{days_number}'))

    return keybard


async def sub_renewal_link_inline(link_for_customer: str, payment_id: int, price: int) -> InlineKeyboardMarkup:
    """Return dynamic inline keyboard with specified payment link as URL for inline button."""
    return InlineKeyboardMarkup().\
        add(InlineKeyboardButton(loc.client.btns['payment_make'].format(price), url=link_for_customer)).\
        add(InlineKeyboardButton(loc.client.btns['payment_check'], callback_data=f'payment-check-{payment_id}')).\
        add(InlineKeyboardButton(loc.client.btns['payment_cancel'], callback_data='payment-cancel'))


menu = ReplyKeyboardMarkup(resize_keyboard=True).\
    add(KeyboardButton(loc.client.btns['sub_renewal'])).\
    add(KeyboardButton(loc.client.btns['sub_status'])).insert(KeyboardButton(loc.client.btns['interfax_test'])).\
    add(KeyboardButton(loc.client.btns['moscow_exchange_test'])).insert(KeyboardButton('Кнопка 5')).insert(KeyboardButton('Кнопка 6'))