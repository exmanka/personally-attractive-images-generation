from aiogram.dispatcher.filters.state import State, StatesGroup


class SendMessage(StatesGroup):
    """FSM states for sending messages to clients via bot."""
    everyone = State()
    selected = State()
    selected_list = State()
