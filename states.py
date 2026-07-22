from aiogram.fsm.state import State, StatesGroup

class Diagnosis(StatesGroup):
    waiting_answer = State()

class OARS(StatesGroup):
    waiting_situation = State()
    waiting_emotion = State()
    waiting_body = State()
    waiting_thought = State()
    waiting_behavior = State()
    waiting_confirmation = State()

class VoiceConfirm(StatesGroup):
    waiting = State()

class BeckTest(StatesGroup):
    waiting_answer = State()

class Tests(StatesGroup):
    waiting = State()

class PremiumChat(StatesGroup):
    active = State()
