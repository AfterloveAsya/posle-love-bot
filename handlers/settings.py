from aiogram import Router, types, F
from aiogram.filters import Command
import db
from config import ADMIN_USER_ID
from keyboards import back_to_menu_kb, settings_menu_kb, time_settings_kb
from loader import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "settings")
async def settings_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ **Настройки**\n\nВыбери раздел:", reply_markup=settings_menu_kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "settings_time")
async def settings_time(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    mh = 6
    eh = 18
    if user_data and "morning_hour" in user_data:
        mh = user_data["morning_hour"]
        eh = user_data["evening_hour"]
    text = f"⏰ **Время рассылки**\n\nСейчас: утро **{mh}:00 UTC** ({mh+3}:00 МСК) / вечер **{eh}:00 UTC** ({eh+3}:00 МСК)\n\nВыбери новое время:"
    await callback.message.edit_text(text, reply_markup=time_settings_kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def set_time(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    morning = int(parts[1])
    evening = int(parts[2])
    db.set_user_time(callback.from_user.id, morning, evening)
    await callback.message.edit_text(
        f"✅ Время сохранено!\n\nУтро: **{morning}:00 UTC** ({morning+3}:00 МСК)\nВечер: **{evening}:00 UTC** ({evening+3}:00 МСК)",
        reply_markup=settings_menu_kb, parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "subscribe")
async def subscribe_info(callback: types.CallbackQuery):
    if db.is_premium(callback.from_user.id):
        await callback.message.edit_text(
            "✅ У тебя активна Premium-подписка. Спасибо, что ты с нами!",
            reply_markup=back_to_menu_kb
        )
        await callback.answer()
        return

    pay_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить 499₽ (месяц)", url="https://b2b.cbrpay.ru/AS1B001960PEAB7E8EURMBD7NVIK1JBJ")],
            [InlineKeyboardButton(text="💳 Оплатить 2990₽ (год)", url="https://b2b.cbrpay.ru/BS1B000S6GJK30P18TFPD4AC31QUTHUU")],
            [InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]
    )
    await callback.message.edit_text(
        "⚙️ **Premium-подписка**\n\n"
        "• Персональные задания каждый день\n"
        "• AI-анализ дневника\n"
        "• Утренние и вечерние сообщения\n\n"
        "После оплаты нажми «Я оплатил», и мы активируем твой доступ.",
        reply_markup=pay_kb, parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: types.CallbackQuery):
    user = callback.from_user
    await callback.message.edit_text(
        "Спасибо! Твоя оплата проверяется. Мы активируем подписку в ближайшее время.",
        reply_markup=back_to_menu_kb
    )
    await bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"🔔 Пользователь @{user.username or 'нет username'} (ID: {user.id}) оплатил подписку. Проверьте и активируйте командой:\n`/activate {user.id}`",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("activate"))
async def cmd_activate(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        if db.activate_premium(user_id, days=365):
            await message.answer(f"Premium активирован для {user_id}")
            try:
                await bot.send_message(user_id, "🎉 Твоя Premium-подписка активирована администратором!")
            except Exception:
                await message.answer("Юзер не найден в чатах (не начинал диалог с ботом).")
        else:
            await message.answer(f"Пользователь {user_id} не найден в БД. Сначала нужно пройти /start.")
    except (IndexError, ValueError):
        await message.answer("Использование: /activate user_id")
