from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import db
import ai_module
from keyboards import main_menu_kb, back_to_menu_kb, diary_menu_kb, premium_upsell_kb
from loader import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

GREETINGS = {"привет", "здравствуй", "здравствуйте", "хай", "hi", "hello", "ку", "даров", "салют", "добрый день", "доброе утро", "добрый вечер", "хелоу", "хелло"}


@router.callback_query(F.data == "diary")
async def diary_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📓 **Дневник рефлексии**\n\nНапиши мне сообщение, и я проанализирую его через AI. Или посмотри свои прошлые записи.",
        reply_markup=diary_menu_kb, parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "diary_write")
async def diary_write(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✏️ Напиши мне сообщение — я проанализирую его и сохраню.",
        reply_markup=back_to_menu_kb
    )
    await callback.answer()


@router.callback_query(F.data == "diary_history")
async def diary_history(callback: types.CallbackQuery):
    entries = db.get_last_entries(callback.from_user.id, limit=5)
    if not entries:
        await callback.message.edit_text("У тебя пока нет записей. Напиши что-нибудь в дневник!", reply_markup=back_to_menu_kb)
        await callback.answer()
        return
    text = "📖 **Мои записи (последние 5):**\n\nНажми на запись, чтобы увидеть ответ AI.\n\n"
    buttons = []
    for e in entries:
        preview = e["entry"][:50] + "..." if len(e["entry"]) > 50 else e["entry"]
        date = e["timestamp"][:10]
        buttons.append([InlineKeyboardButton(text=f"📝 {date}: {preview}", callback_data=f"diary_view_{e['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 В дневник", callback_data="diary")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("diary_view_"))
async def diary_view_entry(callback: types.CallbackQuery):
    entry_id = int(callback.data.split("_")[-1])
    entry = db.get_entry_by_id(entry_id, callback.from_user.id)
    if not entry:
        await callback.answer("Запись не найдена.", show_alert=True)
        return
    text = (
        f"📝 **Запись от {entry['timestamp'][:10]}**\n\n"
        f"**Ты:** {entry['entry']}\n\n"
        f"**🤖 AI:** {entry['response']}"
    )
    if len(text) > 3500:
        text = text[:3500] + "...\n\n(сообщение сокращено)"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку", callback_data="diary_history")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.message(StateFilter(None), F.text)
async def diary_entry(message: types.Message):
    text = message.text.strip().lower()
    if text in GREETINGS or len(text) < 3:
        await message.answer("🌿 Привет! Как твоё настроение сегодня? Можешь рассказать, что на душе, или выбрать пункт в меню.", reply_markup=main_menu_kb)
        return
    if not db.is_premium(message.from_user.id):
        db.save_diary_entry(message.from_user.id, message.text, response="")
        days = db.get_user_days(message.from_user.id)
        if days >= 3:
            await message.answer(
                "📓 **Запись сохранена!**\n\n"
                "Ты уже {days} дней с ботом, и я вижу, как ты стараешься. "
                "Чтобы получить **AI-анализ** каждой записи и персональную обратную связь, "
                "оформи подписку — это поддержит твой путь.".format(days=days),
                reply_markup=premium_upsell_kb(), parse_mode="Markdown"
            )
        else:
            await message.answer(
                "📓 **Запись сохранена!**\n\n"
                "AI-анализ дневника доступен по подписке Premium.\n"
                "Оформить: меню → Настройки → Подписка",
                reply_markup=back_to_menu_kb, parse_mode="Markdown"
            )
        return
    await bot.send_chat_action(message.chat.id, action="typing")
    history = [e["entry"] for e in db.get_last_entries(message.from_user.id, limit=3)]
    username = message.from_user.first_name or message.from_user.username or ""
    last_date = db.get_last_diary_date(message.from_user.id)
    is_first_today = last_date != message.date.strftime("%Y-%m-%d")
    analysis = await ai_module.analyze_diary_entry(message.text, history=history, username=username, is_first_today=is_first_today, user_context=db.get_user_context(message.from_user.id))
    db.save_diary_entry(message.from_user.id, message.text, response=analysis)
    await message.answer(analysis, reply_markup=back_to_menu_kb)
