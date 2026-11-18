from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import Intake, Diagnosis
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import db
from keyboards import main_menu_kb

router = Router()


INTAKE_QUESTIONS = [
    {
        "id": "breakup_date",
        "text": (
            "🔍 **Первичный приём**\n\n"
            "Сколько времени прошло после расставания? "
            "(Ответь: дней, недель, месяцев — например, «2 месяца» или «20 дней»)"
        ),
        "field": "breakup_date"
    },
    {
        "id": "initiator",
        "text": (
            "Кто был инициатором расставания?\n\n"
            "Выбери вариант:"
        ),
        "options": [
            ("Я сам(а)", "я"),
            ("Мой партнёр", "партнер"),
            ("Взаимное решение", "взаимно"),
        ]
    },
    {
        "id": "relationship_duration",
        "text": (
            "Как долго вы были вместе?\n"
            "(Ответь: дней, месяцев, лет — например, «3 года» или «6 месяцев»)"
        ),
        "field": "relationship_duration"
    },
    {
        "id": "children",
        "text": "Были ли у вас дети или совместное имущество?",
        "options": [
            ("Нет", "нет"),
            ("Дети", "дети"),
            ("Имущество", "имущество"),
            ("И то, и другое", "оба"),
        ]
    },
    {
        "id": "previous_breakups",
        "text": (
            "Были ли у тебя серьёзные расставания до этого?\n\n"
            "Это поможет мне понять твой опыт."
        ),
        "options": [
            ("Нет, это первое", "первое"),
            ("Было одно", "одно"),
            ("Было несколько", "несколько"),
        ]
    }
]


@router.message(F.text.startswith("/start"))
async def cmd_start_intake(message: types.Message, state: FSMContext):
    """Перехватываем /start и запускаем первичный приём вместо диагностики"""
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
        "Давай сначала я соберу информацию о твоей ситуации — это займёт 2 минуты."
    )
    await message.answer(welcome_text)
    await state.update_data(intake_index=0, intake_data={})
    await state.set_state(Intake.waiting_breakup_date)
    await ask_intake_question(message, state, 0)


async def ask_intake_question(message: types.Message, state: FSMContext, index: int):
    """Задаёт вопрос анамнеза"""
    if index >= len(INTAKE_QUESTIONS):
        # Все вопросы заданы, переходим на диагностику
        await finish_intake(message, state)
        return
    
    question = INTAKE_QUESTIONS[index]
    
    if "options" in question:
        # Вопрос с кнопками
        buttons = [
            [InlineKeyboardButton(text=opt[0], callback_data=f"intake_{question['id']}_{opt[1]}")]
            for opt in question["options"]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(question["text"], reply_markup=keyboard)
    else:
        # Текстовый ответ
        await message.answer(question["text"])


@router.callback_query(F.data.startswith("intake_"))
async def process_intake_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает ответы на вопросы анамнеза"""
    parts = callback.data.split("_", 2)
    question_id = parts[1]
    answer = parts[2] if len(parts) > 2 else ""
    
    data = await state.get_data()
    intake_data = data.get("intake_data", {})
    intake_data[question_id] = answer
    intake_index = data.get("intake_index", 0)
    
    await state.update_data(intake_data=intake_data, intake_index=intake_index + 1)
    await callback.answer()
    
    # Переходим на следующий вопрос
    await ask_intake_question(callback.message, state, intake_index + 1)


@router.message(Intake.waiting_breakup_date)
async def handle_breakup_date(message: types.Message, state: FSMContext):
    """Сохраняет дату расставания"""
    data = await state.get_data()
    intake_data = data.get("intake_data", {})
    intake_data["breakup_date"] = message.text
    intake_index = data.get("intake_index", 0)
    
    await state.update_data(intake_data=intake_data, intake_index=intake_index + 1)
    await ask_intake_question(message, state, intake_index + 1)


@router.message(Intake.waiting_relationship_duration)
async def handle_relationship_duration(message: types.Message, state: FSMContext):
    """Сохраняет длительность отношений"""
    data = await state.get_data()
    intake_data = data.get("intake_data", {})
    intake_data["relationship_duration"] = message.text
    intake_index = data.get("intake_index", 0)
    
    await state.update_data(intake_data=intake_data, intake_index=intake_index + 1)
    await ask_intake_question(message, state, intake_index + 1)


async def finish_intake(message: types.Message, state: FSMContext):
    """Завершает первичный приём и переходит на диагностику"""
    data = await state.get_data()
    intake_data = data.get("intake_data", {})
    user_id = message.chat.id
    
    # Сохраняем анамнез в БД
    db.save_intake(
        user_id,
        intake_data.get("breakup_date", ""),
        intake_data.get("initiator", ""),
        intake_data.get("relationship_duration", ""),
        intake_data.get("children", ""),
        intake_data.get("previous_breakups", "")
    )
    
    # Спасибо за информацию
    thanks_text = (
        "✅ Спасибо за информацию!\n\n"
        "Теперь давай пройдём диагностику твоего текущего состояния. "
        "Это поможет мне точнее тебя понять и подобрать подходящие техники."
    )
    await message.answer(thanks_text)
    
    # Переходим на диагностику
    await state.update_data(question_index=0, total_score=0)
    await state.set_state(Diagnosis.waiting_answer)
    
    # Импортируем и вызываем функцию из start.py
    from handlers.start import ask_next_question
    await ask_next_question(message, state, is_new_message=True)
