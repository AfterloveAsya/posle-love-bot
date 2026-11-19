from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Diagnosis, OARS
import db
from test_data import DIAGNOSIS_QUESTIONS, calculate_state
from keyboards import main_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


async def start_diagnosis_flow(message: types.Message, state: FSMContext):
    """Запускает диагностику (вызывается из intake.py)"""
    await state.update_data(question_index=0, total_score=0)
    await state.set_state(Diagnosis.waiting_answer)
    await ask_next_question(message, state, is_new_message=True)


async def ask_next_question(message: types.Message, state: FSMContext, is_new_message: bool = False):
    data = await state.get_data()
    index = data.get("question_index", 0)

    if index >= len(DIAGNOSIS_QUESTIONS):
        total = data.get("total_score", 0)
        user_state = calculate_state(total)
        user_id = message.chat.id
        
        # Сохраняем базовый диагноз
        db.save_diagnosis(user_id, user_state, total)
        
        # Импортируем функции для расширенной диагностики
        from diagnosis import calculate_severity, get_therapy_types
        from treatment_plan import generate_treatment_plan
        import json
        
        # Получаем информацию о тяжести
        severity = calculate_severity(total, user_state)
        
        # Получаем рекомендованные методы терапии
        therapies = get_therapy_types(user_state, severity["level"])
        
        # Получаем контекст анамнеза
        intake = db.get_intake(user_id)
        intake_context = ""
        if intake:
            intake_context = f"Время после расставания: {intake.get('breakup_date', '')}; Инициатор: {intake.get('initiator', '')}; Длительность отношений: {intake.get('relationship_duration', '')}"
        
        # Сохраняем полный диагноз
        therapies_json = json.dumps(therapies)
        db.save_diagnosis_report(
            user_id, 
            user_state, 
            total, 
            severity["level"],
            severity["code"],
            severity["description"],
            therapies_json,
            intake_context
        )
        
        # Генерируем и сохраняем план лечения
        treatment_plan = generate_treatment_plan(user_state, severity["level"], intake)
        plan_json = json.dumps(treatment_plan)
        db.save_treatment_plan(user_id, user_state, severity["level"], plan_json)

        # Выводим результат с информацией о тяжести
        result_text = (
            f"🔍 **ДИАГНОСТИЧЕСКИЙ ОТЧЁТ**\n\n"
            f"**Состояние:** {user_state}\n"
            f"**Баллы:** {total}\n"
            f"**Степень тяжести:** {severity['level']}\n\n"
            f"{severity['description']}\n\n"
            f"**Рекомендуемые методы работы:**\n"
        )
        
        for i, therapy in enumerate(therapies, 1):
            result_text += f"{i}. **{therapy['name']}** — {therapy['description']}\n"
        
        result_text += f"\n{severity['recommendation']}"

        db.clear_user_story(user_id)
        await message.answer(result_text)
        
        # Показываем краткий план лечения
        if treatment_plan:
            plan_preview = (
                f"\n📋 **ПЛАН ЛЕЧЕНИЯ**\n\n"
                f"**Краткосрочные цели** ({treatment_plan.get('short_term', {}).get('duration', '')}):\n"
            )
            short_goals = treatment_plan.get('short_term', {}).get('goals', [])
            for goal in short_goals[:2]:  # Показываем первые 2 цели
                plan_preview += f"• {goal.get('goal', '')}\n"
            
            plan_preview += f"\n**Среднесрочные цели** ({treatment_plan.get('mid_term', {}).get('duration', '')}):\n"
            mid_goals = treatment_plan.get('mid_term', {}).get('goals', [])
            for goal in mid_goals[:2]:
                plan_preview += f"• {goal.get('goal', '')}\n"
            
            plan_preview += f"\n(Полный план можно посмотреть командой /план)"
            await message.answer(plan_preview)
        
        await message.answer("Теперь давайте углубимся в твою ситуацию. Я задам тебе несколько вопросов.")
        await state.set_state(OARS.waiting_situation)
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


@router.callback_query(F.data.startswith("diag_answer_"))
async def process_diag_answer(callback: types.CallbackQuery, state: FSMContext):
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    if question_index >= len(DIAGNOSIS_QUESTIONS):
        await callback.answer("Диагностика уже завершена", show_alert=True)
        return
    options = DIAGNOSIS_QUESTIONS[question_index]["options"]
    if answer_index >= len(options):
        await callback.answer("Используй актуальные кнопки", show_alert=True)
        return
    score = options[answer_index][1]
    new_total = data.get("total_score", 0) + score
    await state.update_data(total_score=new_total, question_index=question_index + 1)
    await callback.answer()
    await ask_next_question(callback.message, state)


@router.message(Diagnosis.waiting_answer)
async def diag_text_handler(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    if text in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
    else:
        await message.answer("Пожалуйста, выбери вариант из кнопок ниже 👇")
