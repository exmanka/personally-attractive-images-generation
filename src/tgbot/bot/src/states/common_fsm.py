from aiogram.dispatcher.filters.state import State, StatesGroup


class UserInfo(StatesGroup):
    """FSM states for gathering user information"""
    sex = State()


class Model(StatesGroup):
    """FSM states for model selection and usage."""
    information = State()
    selection = State()
    generation_in_process = State()
    generation_feedback_attractive = State()
    generation_feedback_unattractive = State()
    generation_generate = State()