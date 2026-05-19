from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import OARS
import db
import ai_module
from keyboards import main_menu_kb
from loader import bot

router = Router()


@router.message(OARS.waiting_situation)
async def process_situation(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Ситуация", message.text)
    await message.answer("Какое чувство сейчас самое сильное?")
    await state.set_state(OARS.waiting_emotion)


@router.message(OARS.waiting_emotion)
async def process_emotion(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Эмоции", message.text)
    await message.answer("Где в теле ты ощущаешь эту эмоцию? (например, ком в горле, тяжесть в груди)")
    await state.set_state(OARS.waiting_body)


@router.message(OARS.waiting_body)
async def process_body(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Тело", message.text)
    await message.answer("Какая мысль крутится у тебя в голове чаще всего?")
    await state.set_state(OARS.waiting_thought)


@router.message(OARS.waiting_thought)
async def process_thought(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Мысли", message.text)
    await message.answer("Что ты делаешь, когда становится совсем тяжело? (например, залипаешь в соцсетях, ешь, плачешь)")
    await state.set_state(OARS.waiting_behavior)


@router.message(OARS.waiting_behavior)
async def process_behavior(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Поведение", message.text)
    story = db.get_user_story(message.from_user.id)
    summary = "Вот что я услышал:\n"
    for item in story:
        summary += f"• {item['q']}: {item['a']}\n"
    summary += "\nВсё верно? (напиши «да» или «нет», чтобы уточнить)"
    await message.answer(summary)
    await state.set_state(OARS.waiting_confirmation)


@router.message(OARS.waiting_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower().strip() in ("да", "да.", "да!"):
        if not db.is_premium(message.from_user.id):
            db.clear_user_story(message.from_user.id)
            await state.clear()
            await message.answer(
                "📋 **Экспертный разбор** доступен по подписке Premium.\n\n"
                "Оформить: Настройки → Подписка",
                reply_markup=main_menu_kb, parse_mode="Markdown"
            )
            return
        await message.answer("Спасибо. Я анализирую твою историю, чтобы дать экспертный разбор...")
        story = db.get_user_story(message.from_user.id)
        story_text = "\n".join(f"{s['q']}: {s['a']}" for s in story)
        analysis = await ai_module.expert_analysis(story, user_context=db.get_user_context(message.from_user.id))
        await message.answer(analysis, reply_markup=main_menu_kb)
        user_state = db.get_user_state(message.from_user.id)
        db.save_analysis(
            user_id=message.from_user.id,
            state=user_state["state"] if user_state else "стабилизация",
            score=user_state["score"] if user_state else 0,
            analysis=analysis,
            story=story_text
        )
        db.clear_user_story(message.from_user.id)
        await state.clear()
    elif message.text.lower().strip() in ("нет", "нет.", "нет!", "назад", "меню", "выйти"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
    else:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)


@router.callback_query(F.data == "deep_analysis")
async def deep_analysis(callback: types.CallbackQuery, state: FSMContext):
    user_data = db.get_user_state(callback.from_user.id)
    if not user_data:
        await callback.message.answer("Сначала пройди диагностику через /start.")
        await callback.answer()
        return
    analysis_count = db.get_analysis_count(callback.from_user.id)
    db.clear_user_story(callback.from_user.id)
    if not db.is_premium(callback.from_user.id):
        await callback.message.answer(
            "🔍 **Углублённый разбор** — премиум-функция.\n\n"
            "Оформить подписку: Настройки → Подписка",
            reply_markup=main_menu_kb
        )
        await callback.answer()
        return
    if analysis_count == 0:
        greeting = (
            "Спасибо, что обратился. Сейчас мы начнём с тобой полноценную сессию. "
            "Я буду задавать тебе вопросы, и мы будем углубляться в твою ситуацию: "
            "разберём триггеры, детские травмы, формат отношений, паттерны зависимости. "
            "В конце ты получишь полный разбор.\n\n"
        )
    else:
        greeting = (
            "Рад снова с тобой работать. Мы продолжим углубляться в твою ситуацию. "
            "Ты проходил(а) этот разбор уже {n} раз — каждый новый помогает замечать то, что раньше "
            "ускользало от внимания.\n\n"
        ).format(n=analysis_count + 1)
    await callback.message.answer(
        greeting + "Расскажи, что произошло. Как давно вы расстались? Кто был инициатором?"
    )
    await state.set_state(OARS.waiting_situation)
    await callback.answer()
