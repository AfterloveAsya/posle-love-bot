import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    ReplyKeyboardRemove,
)
import db
import ai_module
import scheduler

BOT_TOKEN = "8746574885:AAEjgDVRSdmv9M_gdgDiH32Ax9RALfiGI0A"
ADMIN_USER_ID = 6433905414

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)


class Diagnosis(StatesGroup):
    waiting_answer = State()


class OARS(StatesGroup):
    waiting_situation = State()
    waiting_emotion = State()
    waiting_body = State()
    waiting_thought = State()
    waiting_behavior = State()
    waiting_confirmation = State()


class BeckTest(StatesGroup):
    waiting_answer = State()


main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Сегодняшнее задание", callback_data="task")],
        [InlineKeyboardButton(text="📓 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="📊 Моё состояние", callback_data="my_state")],
        [InlineKeyboardButton(text="📋 Мои разборы", callback_data="my_analysis")],
        [InlineKeyboardButton(text="🔍 Углублённый разбор", callback_data="deep_analysis")],
        [InlineKeyboardButton(text="📋 Тест Бека", callback_data="beck_test")],
        [InlineKeyboardButton(text="📚 Библиотека техник", callback_data="library")],
        [InlineKeyboardButton(text="🆘 Кризисная помощь", callback_data="crisis")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
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
        [InlineKeyboardButton(text="💎 Подписка", callback_data="subscribe")],
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

TASKS = {
    "кризис": [
        "🌊 «Холодная вода»: Умойся ледяной водой или подержи запястья под холодной струёй 30 секунд. Это снижает тревогу через вегетативную нервную систему.",
        "🌳 «5-4-3-2-1»: Назови 5 вещей, которые видишь, 4 — которые можешь потрогать, 3 — слышишь, 2 — запаха, 1 — вкус. Возвращает в настоящий момент.",
        "💨 «Квадратное дыхание»: Вдох на 4 счёта, задержка на 4, выдох на 4, задержка на 4. Повтори 3-5 раз.",
        "📝 «Выплеск эмоций»: Возьми бумагу и пиши всё, что приходит в голову — гнев, боль, страх. Не оценивай. Потом можно порвать.",
        "🧸 «Внутренний Ребёнок»: Положи руку на сердце и скажи себе: «Я с тобой. Тебе больно, но ты не один. Я выдержу».",
    ],
    "стабилизация": [
        "📖 «Письмо без отправки»: Напиши бывшему партнёру всё, что чувствуешь. Не отправляй. Сохрани или удали.",
        "🌼 «Маленькая радость»: Запланируй сегодня что-то приятное для себя (чашка любимого чая, фильм, прогулка). Сделай это осознанно.",
        "🧘 «Сканирование тела»: Закрой глаза и мысленно пройди вниманием от макушки до пяток, замечая напряжение. Мягко расслабляй каждую зону.",
        "💬 «Аффирмация дня»: Повтори 5 раз: «Я имею право на свои чувства. Я постепенно исцеляюсь. Я ценен/ценна сам(а) по себе».",
        "🌙 «Вечерняя благодарность»: Перед сном вспомни 3 вещи, за которые ты благодарен/на сегодня (даже мелочи). Запиши.",
    ],
    "восстановление": [
        "🎨 «Моё будущее»: Нарисуй или опиши, каким ты видишь своё идеальное утро через год. Какие детали? Кто рядом? Что ты чувствуешь?",
        "🌟 «Сильные стороны»: Напиши 5 своих качеств, которые помогли тебе пережить трудности. Это твоя опора.",
        "📚 «Письмо Внутреннему Ребёнку»: Напиши себе-маленькому слова поддержки и заботы. Что бы ты хотел(а) услышать в детстве?",
        "🔄 «Новый ритуал»: Придумай новое маленькое действие, которое будет символом твоей новой главы (например, заваривать особый чай по утрам).",
        "💎 «Уроки опыта»: Подумай, что важного ты узнал(а) о себе благодаря этим отношениям. Запиши, без осуждения.",
    ],
}

DIAGNOSIS_QUESTIONS = [
    {
        "text": "Вопрос 1/7: Как часто за последнюю неделю ты чувствовал(а) сильную тревогу или панику?",
        "options": [("Почти постоянно", 3), ("Несколько раз в день", 2), ("Пару раз за неделю", 1), ("Не чувствовал(а)", 0)]
    },
    {
        "text": "Вопрос 2/7: Бывает ли, что мысли о бывшем партнёре мешают тебе работать или спать?",
        "options": [("Да, постоянно", 3), ("Часто", 2), ("Редко", 1), ("Нет", 0)]
    },
    {
        "text": "Вопрос 3/7: Хочется ли тебе написать или позвонить бывшему партнёру, несмотря на решение расстаться?",
        "options": [("Очень сильно хочется", 3), ("Иногда возникает желание", 2), ("Скорее нет, чем да", 1), ("Нет, не хочется", 0)]
    },
    {
        "text": "Вопрос 4/7: Чувствуешь ли ты опустошённость или потерю интереса к тому, что раньше радовало?",
        "options": [("Да, я ничего не хочу", 3), ("Часто такое состояние", 2), ("Иногда бывает", 1), ("Я сохранил(а) интерес к жизни", 0)]
    },
    {
        "text": "Вопрос 5/7: Как ты оцениваешь свою самокритику в последние дни?",
        "options": [("Я постоянно виню себя во всём", 3), ("Часто критикую себя", 2), ("Иногда замечаю самокритику", 1), ("Я отношусь к себе бережно", 0)]
    },
    {
        "text": "Вопрос 6/7: Есть ли у тебя хотя бы 1-2 человека, с кем ты можешь открыто поделиться своими переживаниями?",
        "options": [("Нет, я совсем один(на)", 3), ("Есть, но не уверен(а), что могу открыться", 2), ("Есть один близкий человек", 1), ("Да, у меня есть поддержка", 0)]
    },
    {
        "text": "Вопрос 7/7: Видишь ли ты для себя будущее через полгода-год, которое приносит хотя бы каплю надежды?",
        "options": [("Я вообще не вижу будущего", 3), ("Скорее нет, чем да", 2), ("Есть проблески надежды", 1), ("Да, я верю, что всё наладится", 0)]
    }
]


def calculate_state(total_score: int) -> str:
    if total_score >= 15:
        return "кризис"
    elif total_score >= 7:
        return "стабилизация"
    else:
        return "восстановление"


# ===== START =====
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
    await message.answer("🔹", reply_markup=ReplyKeyboardRemove())
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
            ),
        }

        await message.answer(
            result_texts[user_state]
            + "\n\nА теперь давай поговорим. Расскажи, что произошло. Как давно вы расстались? Кто был инициатором?"
        )
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


# ===== OARS DIALOG =====
@dp.message(OARS.waiting_situation)
async def process_situation(message: types.Message, state: FSMContext):
    db.save_user_answer(message.from_user.id, "Ситуация", message.text)
    await message.answer("Какое чувство сейчас самое сильное?")
    await state.set_state(OARS.waiting_emotion)


@dp.message(OARS.waiting_emotion)
async def process_emotion(message: types.Message, state: FSMContext):
    db.save_user_answer(message.from_user.id, "Эмоции", message.text)
    await message.answer("Где в теле ты ощущаешь эту эмоцию? (например, ком в горле, тяжесть в груди)")
    await state.set_state(OARS.waiting_body)


@dp.message(OARS.waiting_body)
async def process_body(message: types.Message, state: FSMContext):
    db.save_user_answer(message.from_user.id, "Тело", message.text)
    await message.answer("Какая мысль крутится у тебя в голове чаще всего?")
    await state.set_state(OARS.waiting_thought)


@dp.message(OARS.waiting_thought)
async def process_thought(message: types.Message, state: FSMContext):
    db.save_user_answer(message.from_user.id, "Мысли", message.text)
    await message.answer("Что ты делаешь, когда становится совсем тяжело? (например, залипаешь в соцсетях, ешь, плачешь)")
    await state.set_state(OARS.waiting_behavior)


@dp.message(OARS.waiting_behavior)
async def process_behavior(message: types.Message, state: FSMContext):
    db.save_user_answer(message.from_user.id, "Поведение", message.text)
    story = db.get_user_story(message.from_user.id)
    summary = "Вот что я услышал:\n"
    for item in story:
        summary += f"• {item['q']}: {item['a']}\n"
    summary += "\nВсё верно? (напиши «да» или «нет», чтобы уточнить)"
    await message.answer(summary)
    await state.set_state(OARS.waiting_confirmation)


@dp.message(OARS.waiting_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower().strip().startswith("да"):
        await message.answer("Спасибо. Я анализирую твою историю, чтобы дать экспертный разбор...")
        story = db.get_user_story(message.from_user.id)
        analysis = await ai_module.expert_analysis(story)
        await message.answer(analysis, reply_markup=main_menu_kb)
        user_state = db.get_user_state(message.from_user.id)
        db.save_analysis(
            user_id=message.from_user.id,
            state=user_state["state"] if user_state else "стабилизация",
            score=user_state["score"] if user_state else 0,
            analysis=analysis
        )
        db.clear_user_story(message.from_user.id)
        await state.clear()
    else:
        await message.answer("Давай уточним. Расскажи ещё раз, что произошло.")
        await state.set_state(OARS.waiting_situation)


# ===== DEEP ANALYSIS FROM MENU =====
@dp.callback_query(F.data == "deep_analysis")
async def deep_analysis(callback: types.CallbackQuery, state: FSMContext):
    user_data = db.get_user_state(callback.from_user.id)
    if not user_data:
        await callback.message.answer("Сначала пройди диагностику через /start.")
        await callback.answer()
        return
    db.clear_user_story(callback.from_user.id)
    await callback.message.answer(
        "Спасибо, что обратился. Сейчас мы начнём с тобой полноценную сессию. "
        "Я буду задавать тебе вопросы, и мы будем углубляться в твою ситуацию: "
        "разберём триггеры, детские травмы, формат отношений, паттерны зависимости. "
        "В конце ты получишь полный разбор.\n\n"
        "Расскажи, что произошло. Как давно вы расстались? Кто был инициатором?"
    )
    await state.set_state(OARS.waiting_situation)
    await callback.answer()


# ===== MAIN MENU =====
@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb)


@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb)
    await callback.answer()


@dp.callback_query(F.data == "my_state")
async def show_my_state(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text("Ты ещё не проходил(а) диагностику.", reply_markup=kb)
    else:
        emoji = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}
        user_state = user_data["state"]
        total = user_data["score"]
        updated = user_data["updated_at"][:10]
        level = "🔴 Кризис" if total >= 15 else ("🟡 Стабилизация" if total >= 7 else "🟢 Восстановление")
        progress_bar = "🟥" * min(total, 21) + "⬜" * (21 - min(total, 21))
        premium = "⭐ Premium" if user_data.get("is_premium") else "—"
        text = (
            f"{emoji.get(user_state, '')} **Твоё состояние:** {level}\n\n"
            f"`{progress_bar}`\nБаллов: {total}/21\n"
            f"Последняя диагностика: {updated}\n"
            f"Статус: {premium}\n\n"
            "Можешь пройти диагностику заново в любой момент."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Пройти заново", callback_data="start_diagnosis")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "my_analysis")
async def show_my_analysis(callback: types.CallbackQuery):
    analysis = db.get_last_analysis(callback.from_user.id)
    if not analysis:
        await callback.message.edit_text(
            "У тебя пока нет сохранённых разборов. Пройди диагностику и ответь на вопросы, чтобы получить экспертный анализ.",
            reply_markup=back_to_menu_kb
        )
        await callback.answer()
        return
    date = analysis["timestamp"][:10]
    state_name = analysis["state"].capitalize()
    text = (
        f"📋 **Твой последний разбор**\n"
        f"Состояние: **{state_name}**\n"
        f"Дата: {date}\n\n"
        f"{analysis['analysis']}"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()


# ===== BECK TEST =====
@dp.callback_query(F.data == "beck_test")
async def beck_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(beck_index=0, beck_score=0)
    await state.set_state(BeckTest.waiting_answer)
    await callback.answer()
    await ask_beck_question(callback.message, state, is_new_message=True)


async def ask_beck_question(message: types.Message, state: FSMContext, is_new_message: bool = False):
    data = await state.get_data()
    index = data.get("beck_index", 0)

    if index >= len(BECK_QUESTIONS):
        total = data.get("beck_score", 0)
        if total <= 13:
            level = "минимальный уровень депрессии"
        elif total <= 19:
            level = "лёгкая депрессия"
        elif total <= 28:
            level = "умеренная депрессия"
        else:
            level = "тяжёлая депрессия"
        text = (
            f"📋 **Тест Бека завершён!**\n\n"
            f"Твой результат: **{total} баллов** — {level}.\n\n"
            "⚠️ Это не диагноз. Тест показывает текущее эмоциональное состояние.\n"
            "Если тебя беспокоит результат — обратись к специалисту."
        )
        await message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
        await state.clear()
        return

    topic, options = BECK_QUESTIONS[index]
    text = f"**Вопрос {index+1}/21:** {topic}\n\n"
    buttons = []
    for i, opt in enumerate(options):
        buttons.append([InlineKeyboardButton(text=opt, callback_data=f"beck_a_{i}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if is_new_message:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("beck_a_"))
async def beck_answer(callback: types.CallbackQuery, state: FSMContext):
    answer = int(callback.data.split("_")[-1])
    data = await state.get_data()
    new_score = data.get("beck_score", 0) + answer
    new_index = data.get("beck_index", 0) + 1
    await state.update_data(beck_score=new_score, beck_index=new_index)
    await callback.answer()
    await ask_beck_question(callback.message, state)


@dp.callback_query(F.data == "task")
async def show_task(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        text = "Сначала пройди диагностику. Нажми /start."
    else:
        state = user_data["state"]
        tasks = TASKS.get(state, TASKS["стабилизация"])
        chosen = random.choice(tasks)
        text = f"📋 **Твоё задание на сегодня:**\n\n{chosen}\n\nВозвращайся завтра за новым!"
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()


# ===== DIARY =====
@dp.callback_query(F.data == "diary")
async def diary_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📓 **Дневник рефлексии**\n\nНапиши мне сообщение, и я проанализирую его через AI. Или посмотри свои прошлые записи.",
        reply_markup=diary_menu_kb, parse_mode="Markdown"
    )
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
    entries = db.get_last_entries(callback.from_user.id, limit=5)
    if not entries:
        text = "У тебя пока нет записей. Напиши что-нибудь в дневник!"
    else:
        lines = []
        for i, e in enumerate(entries, 1):
            preview = e[:80] + "..." if len(e) > 80 else e
            lines.append(f"**{i}.** {preview}")
        text = "📖 **Мои записи:**\n\n" + "\n\n".join(lines)
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()


@dp.message(StateFilter(None))
async def diary_entry(message: types.Message):
    await bot.send_chat_action(message.chat.id, action="typing")
    history = db.get_last_entries(message.from_user.id, limit=3)
    username = message.from_user.first_name or message.from_user.username or ""
    analysis = await ai_module.analyze_diary_entry(message.text, history=history, username=username)
    db.save_diary_entry(message.from_user.id, message.text)
    await message.answer(analysis, reply_markup=back_to_menu_kb)


# ===== SETTINGS =====
@dp.callback_query(F.data == "settings")
async def settings_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ **Настройки**\n\nВыбери раздел:", reply_markup=settings_menu_kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "settings_time")
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


@dp.callback_query(F.data.startswith("time_"))
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


# ===== SUBSCRIBE / MANUAL PAYMENT =====
@dp.callback_query(F.data == "subscribe")
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


@dp.callback_query(F.data == "confirm_payment")
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


# ===== ADMIN =====
@dp.message(Command("activate"))
async def cmd_activate(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        db.activate_premium(user_id, days=365)
        await message.answer(f"Premium активирован для {user_id}")
        await bot.send_message(user_id, "🎉 Твоя Premium-подписка активирована администратором!")
    except (IndexError, ValueError):
        await message.answer("Использование: /activate user_id")


# ===== LIBRARY =====
LIBRARY = {
    "Заземление": (
        "Техники, которые возвращают в «здесь и сейчас» при тревоге:\n\n"
        "🌳 **5-4-3-2-1:** Назови 5 вещей, 4 — потрогать, 3 — услышать, 2 — запаха, 1 — вкус.\n\n"
        "💨 **Квадратное дыхание:** Вдох на 4 — задержка на 4 — выдох на 4 — задержка на 4.\n\n"
        "🧊 **Холодная вода:** Умойся или подержи запястья под холодной водой 30 сек.\n\n"
        "👁 **Фиксация взгляда:** Рассматривай предмет 2 минуты, замечая детали."
    ),
    "Мысли и чувства": (
        "💭 **Работа с мыслями и чувствами**\n\n"
        "📓 **Дневник мыслей:** Записывай ситуацию → мысль → эмоцию → реакцию.\n\n"
        "✉️ **Письмо без отправки:** Напиши человеку всё, что чувствуешь. Не отправляй.\n\n"
        "🔄 **Смена перспективы:** «Что бы я сказал(а) другу в такой ситуации?»\n\n"
        "💬 **Аффирмации:** «Я имею право на свои чувства», «Я ценен/ценна сам(а) по себе»."
    ),
    "Управление триггерами": (
        "Триггер — стимул, вызывающий острую эмоциональную реакцию (напоминание о бывшем, "
        "место, запах, дата).\n\n"
        "📝 **Упражнение:**\n"
        "• Составь список своих триггеров\n"
        "• Для каждого придумай план безопасности\n"
        "• В момент триггера сначала дыши, потом действуй\n\n"
        "💡 **Помни:** триггер — это не опасность, это сигнал. Ты в безопасности сейчас."
    ),
}

SCHEMA_CATEGORIES = {
    "det": {
        "emoji": "🔹",
        "title": "Детские и уязвимые режимы (раненые части)",
        "modes": {
            "Уязвимый ребёнок": "напуганный, покинутый, жаждущий любви и принятия. Чувствует себя никому не нужным, плачет, обижается, боится отвержения и одиночества.",
            "Режим «Жертва»": "ощущение беспомощности, бессилия перед обстоятельствами. Человек верит, что от него ничего не зависит, и пассивно страдает.",
        }
    },
    "cop": {
        "emoji": "🔹",
        "title": "Дезадаптивные копинг-режимы (защитные механизмы, которые вредят)",
        "modes": {
            "Разгневанный защитник": "агрессивная, контролирующая часть. Нападает на других (кричит, обвиняет, ставит ультиматумы) или защищается через злость, когда границы нарушены.",
            "Отстранённый защитник": "убегает от боли через алкоголь, наркотики, азартные игры, порно, онанизм, залипание в сериалах или соцсетях. Отключает чувства, но не решает проблему.",
            "Режим «Спасатель»": "бросается решать чужие проблемы, жертвует собой, помогает даже в ущерб себе. Делает это из тревоги и страха быть ненужным (в отличие от здоровой заботы).",
            "Режим «Ищущий одобрение» (Угодник)": "подстраивается под других, боится сказать «нет», постоянно нуждается в похвале и признании, чтобы чувствовать себя ценным.",
            "Режим «Перфекционист»": "требует от себя идеальности во всём, иначе считает себя «недостаточно хорошим». Приводит к выгоранию, тревоге и самобичеванию при ошибках.",
            "Режим «Преследователь»": "холодно и расчётливо обвиняет, манипулирует, требует справедливости. Может быть направлен на других или на себя. Отличается от Разгневанного защитника отсутствием горячности, более рационален.",
            "Карающий родитель": "внутренний критик, который стыдит, обесценивает, наказывает («ты никчёмный», «сам виноват», «не достоин любви»). Голос значимых взрослых из детства.",
        }
    },
    "health": {
        "emoji": "🔹",
        "title": "Здоровые режимы",
        "modes": {
            "Здоровый взрослый": "сильная, осознанная часть, которая заботится о себе и внутреннем ребёнке, планирует, работает, ставит границы, анализирует свои режимы и управляет ими. Умеет и любить, и требовать, и отдыхать, не впадая в крайности.",
            "Счастливый ребёнок": "спонтанная, радостная часть, способная играть, творить, смеяться, получать удовольствие от простых вещей без чувства вины.",
        }
    },
}

BECK_QUESTIONS = [
    ("Грусть", [
        "Я не чувствую себя несчастным(ой).",
        "Я чувствую себя несчастным(ой).",
        "Я всё время несчастен(на) и не могу выйти из этого состояния.",
        "Я так несчастен(на), что это невыносимо."
    ]),
    ("Пессимизм", [
        "Я смотрю в будущее без уныния.",
        "Я испытываю неуверенность в будущем.",
        "Меня ничего не ждёт в будущем.",
        "Будущее безнадёжно и ничего не изменится к лучшему."
    ]),
    ("Прошлые неудачи", [
        "Я не чувствую себя неудачником.",
        "Я считаю, что терпел(а) больше неудач, чем другие.",
        "Оглядываясь на жизнь, я вижу одни неудачи.",
        "Я чувствую себя полным(ой) неудачником(цей)."
    ]),
    ("Утрата удовольствия", [
        "Я получаю удовольствие от того же, что и раньше.",
        "Я не получаю прежнего удовольствия от вещей.",
        "Я почти не получаю удовольствия от того, что раньше радовало.",
        "Я совсем не получаю удовольствия ни от чего."
    ]),
    ("Чувство вины", [
        "Я не чувствую себя виноватым(ой).",
        "Я виню себя чаще, чем стоило бы.",
        "Я часто чувствую вину за то, что сделал(а) или не сделал(а).",
        "Я постоянно чувствую вину."
    ]),
    ("Ожидание наказания", [
        "Я не чувствую, что заслуживаю наказания.",
        "Я считаю, что могу быть наказан(а).",
        "Я ожидаю наказания.",
        "Я уже наказан(а) и заслужил(а) это."
    ]),
    ("Разочарование в себе", [
        "Я не разочарован(а) в себе.",
        "Я разочарован(а) в себе.",
        "Я испытываю отвращение к себе.",
        "Я ненавижу себя."
    ]),
    ("Самокритика", [
        "Я не критикую себя больше обычного.",
        "Я стал(а) больше критиковать себя.",
        "Я критикую себя за все свои ошибки.",
        "Я виню себя во всём плохом, что происходит."
    ]),
    ("Мысли о самоповреждении", [
        "У меня нет мыслей о самоповреждении.",
        "У меня бывают мысли о самоповреждении, но я их не осуществляю.",
        "Я хочу причинить себе вред.",
        "Я покончу с собой, если представится возможность."
    ]),
    ("Плач", [
        "Я плачу не чаще обычного.",
        "Я плачу чаще, чем раньше.",
        "Я плачу из-за каждой мелочи.",
        "Я хочу плакать, но не могу."
    ]),
    ("Беспокойство", [
        "Я не более взволнован(а), чем обычно.",
        "Я более взволнован(а), чем обычно.",
        "Я очень раздражён(а) и возбуждён(а).",
        "Я настолько взволнован(а), что не могу усидеть на месте."
    ]),
    ("Потеря интереса", [
        "Я не потерял(а) интереса к другим людям.",
        "Я меньше интересуюсь другими людьми.",
        "Я потерял(а) почти весь интерес к другим.",
        "Я совсем не интересуюсь другими."
    ]),
    ("Нерешительность", [
        "Я принимаю решения так же легко, как и раньше.",
        "Мне труднее принимать решения.",
        "Мне очень трудно принимать решения.",
        "Я вообще не могу принимать решения."
    ]),
    ("Ничтожность", [
        "Я не чувствую себя ничтожным(ой).",
        "Я чувствую себя менее ценным(ой), чем другие.",
        "Я чувствую свою никчёмность.",
        "Я чувствую себя совершенно никчёмным(ой)."
    ]),
    ("Потеря энергии", [
        "У меня столько же энергии, как и раньше.",
        "У меня меньше энергии, чем раньше.",
        "У меня недостаточно энергии, чтобы делать что-либо.",
        "У меня совсем нет энергии."
    ]),
    ("Изменения сна", [
        "Я сплю так же хорошо, как и раньше.",
        "Я сплю больше/меньше обычного.",
        "Я просыпаюсь на 1-2 часа раньше и не могу заснуть / сплю намного больше.",
        "Я просыпаюсь на несколько часов раньше и не могу заснуть / сплю почти весь день."
    ]),
    ("Раздражительность", [
        "Я не более раздражителен(на), чем обычно.",
        "Я раздражительнее, чем обычно.",
        "Я раздражён(а) почти всё время.",
        "Я настолько раздражён(а), что не могу ничем заниматься."
    ]),
    ("Изменения аппетита", [
        "Мой аппетит не изменился.",
        "Я ем меньше/больше обычного.",
        "Я ем намного меньше/больше, чем раньше.",
        "У меня совсем нет аппетита / я постоянно ем."
    ]),
    ("Трудности концентрации", [
        "Я концентрируюсь так же хорошо, как и раньше.",
        "Мне труднее концентрироваться.",
        "Мне очень трудно сосредоточиться на чём-либо.",
        "Я вообще не могу концентрироваться."
    ]),
    ("Усталость", [
        "Я устаю не больше обычного.",
        "Я устаю быстрее обычного.",
        "Я устаю от почти всего, что делаю.",
        "Я слишком устал(а), чтобы делать что-либо."
    ]),
    ("Потеря интереса к сексу", [
        "Мой интерес к сексу не изменился.",
        "Я меньше интересуюсь сексом, чем раньше.",
        "Мой интерес к сексу значительно снизился.",
        "Я совсем потерял(а) интерес к сексу."
    ]),
]


@dp.callback_query(F.data == "library")
async def library_menu(callback: types.CallbackQuery):
    lib_buttons = [[InlineKeyboardButton(text=name, callback_data=f"lib_{name}")] for name in LIBRARY.keys()]
    lib_buttons.append([InlineKeyboardButton(text="🧠 Схематерапия: режимы", callback_data="lib_schema")])
    lib_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=lib_buttons)
    await callback.message.edit_text("📚 **Библиотека техник**\n\nВыбери тему:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


# ===== SCHEMA THERAPY SUBMENU =====
def build_schema_menu_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔹 Детские и уязвимые режимы", callback_data="lib_schema_det")],
            [InlineKeyboardButton(text="🔹 Дезадаптивные копинг-режимы", callback_data="lib_schema_cop")],
            [InlineKeyboardButton(text="🔹 Здоровые режимы", callback_data="lib_schema_health")],
            [InlineKeyboardButton(text="🔙 В библиотеку", callback_data="library")],
        ]
    )
    return kb


@dp.callback_query(F.data == "lib_schema")
async def schema_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🧠 **Схематерапия: режимы**\n\n"
        "В схема-терапии выделяют три группы режимов — состояний, в которых мы можем находиться. "
        "Выбери группу, чтобы изучить каждый режим.",
        reply_markup=build_schema_menu_kb(), parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "lib_schema_det")
async def schema_det(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["det"]
    text = f"{cat['emoji']} **{cat['title']}**\n\n"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lib_schema_show_det_{name}")]
            for name in cat["modes"].keys()
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in cat["modes"].items():
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "lib_schema_cop")
async def schema_cop(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["cop"]
    text = f"{cat['emoji']} **{cat['title']}**\n\n"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lib_schema_show_cop_{name}")]
            for name in cat["modes"].keys()
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in cat["modes"].items():
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "lib_schema_health")
async def schema_health(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["health"]
    text = f"{cat['emoji']} **{cat['title']}**\n\n"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lib_schema_show_health_{name}")]
            for name in cat["modes"].keys()
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in cat["modes"].items():
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("lib_schema_show_"))
async def schema_show_mode(callback: types.CallbackQuery):
    parts = callback.data.split("_", 4)
    cat_key = parts[3]
    mode_name = parts[4]
    cat = SCHEMA_CATEGORIES.get(cat_key)
    if cat and mode_name in cat["modes"]:
        content = f"🧠 **{mode_name}**\n\n{cat['modes'][mode_name]}"
    else:
        content = "Режим не найден."
    await callback.message.edit_text(
        content,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"lib_schema_{cat_key}")]
        ]), parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("lib_"))
async def show_library_article(callback: types.CallbackQuery):
    topic = callback.data[4:]
    content = LIBRARY.get(topic, "Скоро здесь будет подробная статья.")
    await callback.message.edit_text(f"📖 **{topic}**\n\n{content}", reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()


# ===== CRISIS =====
@dp.callback_query(F.data == "crisis")
async def crisis_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🆘 **Экстренная помощь**\n\n"
        "Сделай прямо сейчас:\n"
        "1. Умойся холодной водой или подержи руки под холодной водой.\n"
        "2. Сделай 5 глубоких вдохов (вдох на 4 счёта, выдох на 6).\n"
        "3. Повторяй: «Я в безопасности. Это чувство пройдёт».\n\n"
        "📞 **Телефоны доверия (Россия):**\n"
        "• 8 (800) 333-44-34\n"
        "• 8 (800) 2000-122 (для детей и подростков)\n"
        "• 112 — экстренная служба",
        reply_markup=back_to_menu_kb, parse_mode="Markdown"
    )
    await callback.answer()


# ===== MAIN =====
async def main():
    db.init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать сначала"),
        BotCommand(command="menu", description="Главное меню"),
    ])
    asyncio.create_task(scheduler.scheduled_task(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
