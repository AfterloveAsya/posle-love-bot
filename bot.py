import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import db
import ai_module
import scheduler

BOT_TOKEN = "8746574885:AAEjgDVRSdmv9M_gdgDiH32Ax9RALfiGI0A"

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

class Diagnosis(StatesGroup):
    waiting_answer = State()

# ===== КЛАВИАТУРЫ =====
main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Задание", callback_data="task")],
        [InlineKeyboardButton(text="📓 Дневник", callback_data="diary_menu")],
        [InlineKeyboardButton(text="📊 Моё состояние", callback_data="my_state")],
        [InlineKeyboardButton(text="📚 Библиотека техник", callback_data="library")],
        [InlineKeyboardButton(text="🆘 Кризисная помощь", callback_data="crisis")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
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

diary_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Написать в дневник", callback_data="diary_write")],
        [InlineKeyboardButton(text="📖 Мои записи", callback_data="diary_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
)

settings_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Время рассылки", callback_data="settings_time")],
        [InlineKeyboardButton(text="⚙️ Подписка", callback_data="subscribe")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
)

time_settings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🕐 8:00 / 20:00", callback_data="time_8_20")],
        [InlineKeyboardButton(text="🕑 9:00 / 21:00", callback_data="time_9_21")],
        [InlineKeyboardButton(text="🕒 10:00 / 22:00", callback_data="time_10_22")],
        [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings")]
    ]
)

library_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🧸 Внутренний Ребёнок", callback_data="lib_child")],
        [InlineKeyboardButton(text="🧘 Заземление", callback_data="lib_ground")],
        [InlineKeyboardButton(text="💭 Мысли и чувства", callback_data="lib_thoughts")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
)

# ===== БАЗА ЗАДАНИЙ =====
TASKS = {
    "кризис": [
        "🌊 «Холодная вода»: Умойся ледяной водой или подержи запястья под холодной струёй 30 секунд. Это снижает тревогу через вегетативную нервную систему.",
        "🌳 «5-4-3-2-1»: Назови 5 вещей, которые видишь, 4 — которые можешь потрогать, 3 — слышишь, 2 — запаха, 1 — вкус. Возвращает в настоящий момент.",
        "💨 «Квадратное дыхание»: Вдох на 4 счёта, задержка на 4, выдох на 4, задержка на 4. Повтори 3-5 раз.",
        "📝 «Выплеск эмоций»: Возьми бумагу и пиши всё, что приходит в голову — гнев, боль, страх. Не оценивай. Потом можно порвать.",
        "🧸 «Внутренний Ребёнок»: Положи руку на сердце и скажи себе: «Я с тобой. Тебе больно, но ты не один. Я выдержу»."
    ],
    "стабилизация": [
        "📖 «Письмо без отправки»: Напиши бывшему партнёру всё, что чувствуешь. Не отправляй. Сохрани или удали.",
        "🌼 «Маленькая радость»: Запланируй сегодня что-то приятное для себя (чашка любимого чая, фильм, прогулка). Сделай это осознанно.",
        "🧘 «Сканирование тела»: Закрой глаза и мысленно пройди вниманием от макушки до пяток, замечая напряжение. Мягко расслабляй каждую зону.",
        "💬 «Аффирмация дня»: Повтори 5 раз: «Я имею право на свои чувства. Я постепенно исцеляюсь. Я ценен/ценна сам(а) по себе».",
        "🌙 «Вечерняя благодарность»: Перед сном вспомни 3 вещи, за которые ты благодарен/на сегодня (даже мелочи). Запиши."
    ],
    "восстановление": [
        "🎨 «Моё будущее»: Нарисуй или опиши, каким ты видишь своё идеальное утро через год. Какие детали? Кто рядом? Что ты чувствуешь?",
        "🌟 «Сильные стороны»: Напиши 5 своих качеств, которые помогли тебе пережить трудности. Это твоя опора.",
        "📚 «Письмо Внутреннему Ребёнку»: Напиши себе-маленькому слова поддержки и заботы. Что бы ты хотел(а) услышать в детстве?",
        "🔄 «Новый ритуал»: Придумай новое маленькое действие, которое будет символом твоей новой главы (например, заваривать особый чай по утрам).",
        "💎 «Уроки опыта»: Подумай, что важного ты узнал(а) о себе благодаря этим отношениям. Запиши, без осуждения."
    ]
}

# ===== ВОПРОСЫ ДИАГНОСТИКИ =====
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

# ===== КОМАНДЫ =====
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
        "⚠️ Важно: я не заменяю профессионального психолога.\n\n"
        "Всё анонимно. Продолжая, ты принимаешь политику конфиденциальности.\n\n"
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
        db.save_diagnosis(message.chat.id, user_state, total)

        result_texts = {
            "кризис": (
                "🔴 Твой результат: кризисное состояние.\n\n"
                "Сейчас тебе особенно тяжело. Это нормально — испытывать такую боль после расставания. "
                "В ближайшие дни я буду присылать тебе щадящие техники заземления. Помни: это пройдёт."
            ),
            "стабилизация": (
                "🟡 Твой результат: стабилизация.\n\n"
                "Ты уже начал(а) справляться, но боль ещё возвращается. "
                "Мы будем работать над укреплением внутренней опоры."
            ),
            "восстановление": (
                "🟢 Твой результат: восстановление.\n\n"
                "Ты прошёл(а) самый сложный этап. Ресурсы для роста уже есть. "
                "Я помогу тебе углубить понимание себя и вернуть радость жизни."
            )
        }

        await message.answer(
            result_texts[user_state] + "\n\nНажми «В главное меню», чтобы начать.",
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

# ===== НАВИГАЦИЯ =====
@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb)
    await callback.answer()

# ===== ЗАДАНИЕ =====
@dp.callback_query(F.data == "task")
async def show_task(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        text = "Сначала пройди диагностику. Нажми /start."
        await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    else:
        state = user_data["state"]
        tasks = TASKS.get(state, TASKS["стабилизация"])
        chosen = random.choice(tasks)
        text = f"📋 **Твоё задание на сегодня:**\n\n{chosen}"
        await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()

# ===== ДНЕВНИК =====
@dp.callback_query(F.data == "diary_menu")
async def diary_menu(callback: types.CallbackQuery):
    text = "📓 **Дневник рефлексии**\n\nНапиши мне сообщение, и я проанализирую его через AI. Или посмотри свои прошлые записи."
    await callback.message.edit_text(text, reply_markup=diary_menu_kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "diary_write")
async def diary_write(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✏️ Напиши мне сообщение — я проанализирую его и сохраню.",
        reply_markup=back_to_menu_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "diary_history")
async def diary_history(callback: types.CallbackQuery):
    entries = db.get_diary_entries(callback.from_user.id)
    if not entries:
        text = "У тебя пока нет записей. Напиши что-нибудь в дневник!"
    else:
        lines = []
        for i, e in enumerate(entries, 1):
            date = e["created_at"][:10]
            preview = e["text"][:80] + "..." if len(e["text"]) > 80 else e["text"]
            lines.append(f"**{i}. {date}**\n{preview}")
        text = "📖 **Мои записи:**\n\n" + "\n\n".join(lines)
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()

# ===== МОЁ СОСТОЯНИЕ + ПРОГРЕСС =====
@dp.callback_query(F.data == "my_state")
async def show_my_state(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        text = "Ты ещё не проходил(а) диагностику. Начать?",
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
            ]
        )
        await callback.message.edit_text(text[0], reply_markup=kb)
    else:
        state_emoji = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}
        state_name = user_data["state"]
        score = user_data["score"]
        updated = user_data["updated_at"][:10]

        total = score
        level = "🔴 Кризис" if total >= 15 else ("🟡 Стабилизация" if total >= 7 else "🟢 Восстановление")

        progress_bar = "🟥" * min(total, 21) + "⬜" * (21 - min(total, 21))

        text = (
            f"{state_emoji.get(state_name, '')} **Твоё состояние:** {level}\n\n"
            f"`{progress_bar}`\n"
            f"Баллов: {total}/21\n"
            f"Последняя диагностика: {updated}\n\n"
            "Можешь пройти диагностику заново в любой момент."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Пройти заново", callback_data="start_diagnosis")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
            ]
        )
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# ===== БИБЛИОТЕКА ТЕХНИК =====
@dp.callback_query(F.data == "library")
async def library_menu(callback: types.CallbackQuery):
    text = "📚 **Библиотека техник**\n\nВыбери тему:"
    await callback.message.edit_text(text, reply_markup=library_menu_kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "lib_child")
async def lib_child(callback: types.CallbackQuery):
    text = (
        "🧸 **Внутренний Ребёнок**\n\n"
        "В схема-терапии есть понятие «Уязвимый Ребёнок» — часть нас, которая хранит "
        "детские боли и потребности.\n\n"
        "**Как работать:**\n"
        "• Представь себя в детстве. Что бы ты хотел(а) услышать?\n"
        "• Напиши письмо себе-ребёнку со словами поддержки\n"
        "• Положи руку на сердце и скажи: «Я с тобой»\n\n"
        "Практика: закрой глаза, вспомни себя в 5-7 лет. Что на тебе надето? "
        "Что ты чувствуешь? Мысленно обними этого ребёнка."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "lib_ground")
async def lib_ground(callback: types.CallbackQuery):
    text = (
        "🧘 **Заземление**\n\n"
        "Техники, которые возвращают в «здесь и сейчас» при тревоге:\n\n"
        "**5-4-3-2-1:** Назови 5 вещей, которые видишь, 4 — которые можешь потрогать, "
        "3 — слышишь, 2 — запаха, 1 — вкус.\n\n"
        "**Квадратное дыхание:** Вдох на 4 счёта, задержка на 4, выдох на 4, задержка на 4.\n\n"
        "**Холодная вода:** Умойся или подержи запястья под холодной водой 30 секунд.\n\n"
        "**Фиксация взгляда:** Выбери предмет и рассматривай его 2 минуты, "
        "замечая каждую деталь."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

@dp.callback_query(F.data == "lib_thoughts")
async def lib_thoughts(callback: types.CallbackQuery):
    text = (
        "💭 **Работа с мыслями и чувствами**\n\n"
        "**Дневник мыслей:** Записывай ситуацию → мысль → эмоцию → реакцию. "
        "Это поможет заметить повторяющиеся паттерны.\n\n"
        "**Письмо без отправки:** Напиши человеку всё, что чувствуешь. "
        "Не отправляй. Просто дай выход эмоциям.\n\n"
        "**Смена перспективы:** Спроси себя: «Что бы я сказал(а) другу "
        "в такой ситуации?» Отнесись к себе так же бережно.\n\n"
        "**Аффирмации:** «Я имею право на свои чувства», «Я ценен/ценна сам(а) по себе», "
        "«Это чувство временно»."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb)
    await callback.answer()

# ===== КРИЗИСНАЯ ПОМОЩЬ =====
@dp.callback_query(F.data == "crisis")
async def crisis_help(callback: types.CallbackQuery):
    text = (
        "🆘 **Экстренная помощь**\n\n"
        "Сделай прямо сейчас:\n"
        "1. Умойся холодной водой или подержи руки под холодной водой.\n"
        "2. Сделай 5 глубоких вдохов (вдох на 4 счёта, выдох на 6).\n"
        "3. Повторяй: «Я в безопасности. Это чувство пройдёт».\n\n"
        "📞 **Телефоны доверия (Россия):**\n"
        "• 8 (800) 333-44-34\n"
        "• 8 (800) 2000-122 (для детей и подростков)\n"
        "• 112 — экстренная служба\n\n"
        "Пожалуйста, обратись к специалисту, если чувствуешь, что не справляешься."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()

# ===== НАСТРОЙКИ =====
@dp.callback_query(F.data == "settings")
async def settings_menu(callback: types.CallbackQuery):
    text = "⚙️ **Настройки**\n\nВыбери раздел:"
    await callback.message.edit_text(text, reply_markup=settings_menu_kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "settings_time")
async def settings_time(callback: types.CallbackQuery):
    settings = db.get_settings(callback.from_user.id)
    text = (
        f"⏰ **Время рассылки**\n\n"
        f"Сейчас: утро **{settings['morning_hour']}:00 UTC** / вечер **{settings['evening_hour']}:00 UTC**\n"
        f"(МСК: утро **{settings['morning_hour'] + 3}:00** / вечер **{settings['evening_hour'] + 3}:00**)\n\n"
        "Выбери новое время:"
    )
    await callback.message.edit_text(text, reply_markup=time_settings_kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("time_"))
async def set_time(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    morning = int(parts[1])
    evening = int(parts[2])
    db.save_settings(callback.from_user.id, morning, evening)
    await callback.message.edit_text(
        f"✅ Время сохранено!\n\n"
        f"Утро: **{morning}:00 UTC** ({morning + 3}:00 МСК)\n"
        f"Вечер: **{evening}:00 UTC** ({evening + 3}:00 МСК)",
        reply_markup=settings_menu_kb,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "subscribe")
async def subscribe_info(callback: types.CallbackQuery):
    text = (
        "⚙️ **Подписка**\n\n"
        "**Бесплатно:**\n"
        "• Диагностика состояния\n"
        "• Базовые техники и кризисная помощь\n"
        "• AI-анализ дневника\n"
        "• Утренние/вечерние напоминания\n\n"
        "**Premium (скоро):**\n"
        "• Персональные задания каждый день\n"
        "• Расширенный AI-анализ\n"
        "• Приоритетная поддержка\n\n"
        "Сейчас весь функционал бесплатный."
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()

# ===== AI-АНАЛИЗ ДНЕВНИКА =====
@dp.message()
async def diary_entry(message: types.Message):
    await bot.send_chat_action(message.chat.id, action="typing")
    analysis = await ai_module.analyze_diary_entry(message.text)
    db.save_diary_entry(message.from_user.id, message.text, analysis)
    await message.answer(
        analysis,
        reply_markup=back_to_menu_kb
    )

# ===== ЗАПУСК =====
async def main():
    db.init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать сначала"),
        BotCommand(command="menu", description="Главное меню")
    ])
    asyncio.create_task(scheduler.scheduled_task(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
