import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8746574885:AAEjgDVRSdmv9M_gdgDiH32Ax9RALfiGI0A"
# =====================

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

class Diagnosis(StatesGroup):
    waiting_answer = State()

main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Сегодняшнее задание", callback_data="task")],
        [InlineKeyboardButton(text="📓 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="📚 Библиотека техник", callback_data="library")],
        [InlineKeyboardButton(text="🆘 Кризисная помощь", callback_data="crisis")],
        [InlineKeyboardButton(text="⚙️ Подписка", callback_data="subscribe")]
    ]
)

back_to_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
    ]
)

start_diagnosis_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")]
    ]
)

DIAGNOSIS_QUESTIONS = [
    {
        "text": "Вопрос 1/7: Как часто за последнюю неделю ты чувствовал(а) сильную тревогу или панику?",
        "options": [
            ("Почти постоянно", 3),
            ("Несколько раз в день", 2),
            ("Пару раз за неделю", 1),
            ("Не чувствовал(а)", 0)
        ]
    },
    {
        "text": "Вопрос 2/7: Бывает ли, что мысли о бывшем партнёре мешают тебе работать или спать?",
        "options": [
            ("Да, постоянно", 3),
            ("Часто", 2),
            ("Редко", 1),
            ("Нет", 0)
        ]
    },
    {
        "text": "Вопрос 3/7: Хочется ли тебе написать или позвонить бывшему партнёру, несмотря на решение расстаться?",
        "options": [
            ("Очень сильно хочется", 3),
            ("Иногда возникает желание", 2),
            ("Скорее нет, чем да", 1),
            ("Нет, не хочется", 0)
        ]
    },
    {
        "text": "Вопрос 4/7: Чувствуешь ли ты опустошённость или потерю интереса к тому, что раньше радовало?",
        "options": [
            ("Да, я ничего не хочу", 3),
            ("Часто такое состояние", 2),
            ("Иногда бывает", 1),
            ("Я сохранил(а) интерес к жизни", 0)
        ]
    },
    {
        "text": "Вопрос 5/7: Как ты оцениваешь свою самокритику в последние дни?",
        "options": [
            ("Я постоянно виню себя во всём", 3),
            ("Часто критикую себя", 2),
            ("Иногда замечаю самокритику", 1),
            ("Я отношусь к себе бережно", 0)
        ]
    },
    {
        "text": "Вопрос 6/7: Есть ли у тебя хотя бы 1-2 человека, с кем ты можешь открыто поделиться своими переживаниями?",
        "options": [
            ("Нет, я совсем один(на)", 3),
            ("Есть, но не уверен(а), что могу открыться", 2),
            ("Есть один близкий человек", 1),
            ("Да, у меня есть поддержка", 0)
        ]
    },
    {
        "text": "Вопрос 7/7: Видишь ли ты для себя будущее через полгода-год, которое приносит хотя бы каплю надежды?",
        "options": [
            ("Я вообще не вижу будущего", 3),
            ("Скорее нет, чем да", 2),
            ("Есть проблески надежды", 1),
            ("Да, я верю, что всё наладится", 0)
        ]
    }
]

def calculate_state(total_score: int) -> str:
    if total_score >= 15:
        return "кризис"
    elif total_score >= 7:
        return "стабилизация"
    else:
        return "восстановление"

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name or "Дорогой друг"
    welcome_text = (
        f"🌿 Привет, {user_name}!\n\n"
        "Я бот «После любви» — твой анонимный помощник, созданный на основе психологии и схема-терапии.\n\n"
        "Я помогу тебе:\n"
        "• Понять своё состояние\n"
        "• Получать ежедневные поддерживающие задания\n"
        "• Вести дневник рефлексии с AI-анализом\n"
        "• Найти техники самопомощи в трудную минуту\n\n"
        "⚠️ Важно: я не заменяю профессионального психолога. При серьёзных состояниях обратись к специалисту.\n\n"
        "Всё анонимно. Твои данные не передаются третьим лицам.\n"
        "Продолжая, ты принимаешь политику конфиденциальности.\n\n"
        "Давай начнём с диагностики твоего состояния."
    )
    await message.answer(welcome_text, reply_markup=start_diagnosis_kb)

@dp.callback_query(F.data == "start_diagnosis")
async def start_diagnosis(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(question_index=0, total_score=0)
    await state.set_state(Diagnosis.waiting_answer)
    await callback.answer()
    await ask_next_question(callback.message, state, is_new_message=True)

async def ask_next_question(message: types.Message, state: FSMContext, is_new_message: bool = False):
    data = await state.get_data()
    index = data.get("question_index", 0)

    if index >= len(DIAGNOSIS_QUESTIONS):
        total = data.get("total_score", 0)
        user_state = calculate_state(total)

        result_texts = {
            "кризис": (
                "🔴 Твой результат: кризисное состояние.\n\n"
                "Сейчас тебе особенно тяжело. Это нормально — испытывать такую боль после расставания. "
                "В ближайшие дни я буду присылать тебе щадящие техники заземления, которые помогут "
                "пережить самые острые моменты. Помни: это пройдёт."
            ),
            "стабилизация": (
                "🟡 Твой результат: стабилизация.\n\n"
                "Ты уже начал(а) справляться, но боль ещё возвращается. "
                "Мы будем работать над укреплением внутренней опоры и разбором повторяющихся мыслей."
            ),
            "восстановление": (
                "🟢 Твой результат: восстановление.\n\n"
                "Ты прошёл(а) самый сложный этап. Это не значит, что всё идеально, но ресурсы для роста уже есть. "
                "Я помогу тебе углубить понимание себя и вернуть радость жизни."
            )
        }

        await message.answer(
            result_texts[user_state] + "\n\nНажми кнопку «В главное меню», чтобы начать.",
            reply_markup=back_to_menu_kb
        )
        await state.clear()
        return

    question = DIAGNOSIS_QUESTIONS[index]
    buttons = [
        [InlineKeyboardButton(text=opt[0], callback_data=f"diag_answer_{i}")]
        for i, opt in enumerate(question["options"])
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if is_new_message:
        await message.answer(question["text"], reply_markup=keyboard)
    else:
        await message.edit_text(question["text"], reply_markup=keyboard)

@dp.callback_query(F.data.startswith("diag_answer_"))
async def process_diag_answer(callback: types.CallbackQuery, state: FSMContext):
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    question_index = data.get("question_index", 0)

    score = DIAGNOSIS_QUESTIONS[question_index]["options"][answer_index][1]
    new_total = data.get("total_score", 0) + score

    await state.update_data(total_score=new_total, question_index=question_index + 1)
    await callback.answer()
    await ask_next_question(callback.message, state)

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb)

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "task")
async def show_task(callback: types.CallbackQuery):
    text = (
        "📋 Твоё задание на сегодня:\n\n"
        "«Заземление через 5 чувств»\n\n"
        "Найди вокруг себя и мысленно назови:\n"
        "5 вещей, которые ты видишь,\n"
        "4 вещи, которые ты можешь потрогать,\n"
        "3 звука, которые ты слышишь,\n"
        "2 запаха, которые ты ощущаешь,\n"
        "1 вкус.\n\n"
        "Это поможет вернуться в «здесь и сейчас»."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "diary")
async def diary_menu(callback: types.CallbackQuery):
    text = "📓 Дневник рефлексии\n\nНапиши мне сообщение, и я сохраню его. Для анализа просто напиши текст или пришли голосовое. (AI-анализ будет добавлен позже)"
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "library")
async def library_menu(callback: types.CallbackQuery):
    text = "📚 Библиотека техник\n\nЗдесь скоро появятся статьи и аудио по темам: Уязвимый Ребёнок, Карающий родитель, Заземление и другие."
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "crisis")
async def crisis_help(callback: types.CallbackQuery):
    text = (
        "🆘 Экстренная помощь\n\n"
        "Сделай прямо сейчас:\n"
        "1. Умойся холодной водой или подержи руки под холодной водой.\n"
        "2. Сделай 5 глубоких вдохов (вдох на 4 счёта, выдох на 6).\n"
        "3. Повторяй: «Я в безопасности. Это чувство пройдёт».\n\n"
        "📞 Телефоны доверия (Россия):\n"
        "• 8 (800) 333-44-34\n"
        "• 8 (800) 2000-122 (для детей и подростков)\n"
        "• 112 — экстренная служба\n\n"
        "Пожалуйста, обратись к специалисту, если чувствуешь, что не справляешься."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "subscribe")
async def subscribe_info(callback: types.CallbackQuery):
    text = (
        "⚙️ Подписка\n\n"
        "Бесплатный функционал:\n"
        "• Диагностика состояния\n"
        "• Базовые техники и кризисная помощь\n\n"
        "Premium (2990 руб./год или 499 руб./мес.):\n"
        "• Персональные задания каждый день\n"
        "• AI-анализ дневника\n"
        "• Утренние и вечерние поддерживающие сообщения\n\n"
        "Подписка будет доступна позже."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.message()
async def diary_entry(message: types.Message):
    await message.answer("Запись сохранена. Спасибо, что поделился. 💙", reply_markup=back_to_menu_kb)

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать сначала"),
        BotCommand(command="menu", description="Главное меню")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
