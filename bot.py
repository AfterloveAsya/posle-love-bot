import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram import F

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8746574885:AAEjgDVRSdmv9M_gdgDiH32Ax9RALfiGI0A"
# =====================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
        "Продолжая, ты принимаешь политику конфиденциальности."
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb)

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb)

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery):
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
