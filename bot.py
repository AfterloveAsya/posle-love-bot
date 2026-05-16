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


class Tests(StatesGroup):
    waiting = State()


LUSCHER_COLORS = [
    ("🔴", "Красный"),
    ("🟡", "Жёлтый"),
    ("🟢", "Зелёный"),
    ("🔵", "Синий"),
    ("🟣", "Фиолетовый"),
    ("🟤", "Коричневый"),
    ("⬜", "Серый"),
    ("⬛", "Чёрный"),
]


main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Сегодняшнее задание", callback_data="task")],
        [InlineKeyboardButton(text="📓 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="📊 Моё состояние", callback_data="my_state")],
        [InlineKeyboardButton(text="📋 Мои разборы", callback_data="my_analysis")],
        [InlineKeyboardButton(text="🔍 Углублённый разбор", callback_data="deep_analysis")],
        [InlineKeyboardButton(text="📋 Тесты", callback_data="tests_menu")],
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


@dp.message(Diagnosis.waiting_answer)
async def diag_text_handler(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    if text in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
    else:
        await message.answer("Пожалуйста, выбери вариант из кнопок ниже 👇")


# ===== OARS DIALOG =====
@dp.message(OARS.waiting_situation)
async def process_situation(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Ситуация", message.text)
    await message.answer("Какое чувство сейчас самое сильное?")
    await state.set_state(OARS.waiting_emotion)


@dp.message(OARS.waiting_emotion)
async def process_emotion(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Эмоции", message.text)
    await message.answer("Где в теле ты ощущаешь эту эмоцию? (например, ком в горле, тяжесть в груди)")
    await state.set_state(OARS.waiting_body)


@dp.message(OARS.waiting_body)
async def process_body(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Тело", message.text)
    await message.answer("Какая мысль крутится у тебя в голове чаще всего?")
    await state.set_state(OARS.waiting_thought)


@dp.message(OARS.waiting_thought)
async def process_thought(message: types.Message, state: FSMContext):
    if message.text.strip().lower() in ("нет", "назад", "меню", "не хочу", "выйти", "отмена"):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_menu_kb)
        return
    db.save_user_answer(message.from_user.id, "Мысли", message.text)
    await message.answer("Что ты делаешь, когда становится совсем тяжело? (например, залипаешь в соцсетях, ешь, плачешь)")
    await state.set_state(OARS.waiting_behavior)


@dp.message(OARS.waiting_behavior)
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


@dp.message(OARS.waiting_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower().strip() in ("да", "да.", "да!"):
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


# ===== DEEP ANALYSIS FROM MENU =====
@dp.callback_query(F.data == "deep_analysis")
async def deep_analysis(callback: types.CallbackQuery, state: FSMContext):
    user_data = db.get_user_state(callback.from_user.id)
    if not user_data:
        await callback.message.answer("Сначала пройди диагностику через /start.")
        await callback.answer()
        return
    analysis_count = db.get_analysis_count(callback.from_user.id)
    db.clear_user_story(callback.from_user.id)
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
        user_state = user_data.get("state")
        if not user_state:
            tb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text("Ты ещё не проходил(а) диагностику.", reply_markup=tb)
            await callback.answer()
            return
        total = user_data["score"] or 0
        updated = user_data.get("updated_at", "")[:10] if user_data.get("updated_at") else "—"
        level = "🔴 Кризис" if total >= 15 else ("🟡 Стабилизация" if total >= 7 else "🟢 Восстановление")
        progress_bar = "🟥" * min(total, 21) + "⬜" * (21 - min(total, 21))
        premium = "⭐ Premium" if db.is_premium(callback.from_user.id) else "—"
        diary_n = db.get_diary_count(callback.from_user.id)
        analysis_n = db.get_analysis_count(callback.from_user.id)
        streak = db.get_streak_count(callback.from_user.id)
        diag_log = db.get_diagnosis_log(callback.from_user.id, limit=5)

        text = (
            f"{emoji.get(user_state, '')} **Твоё состояние:** {level}\n\n"
            f"`{progress_bar}`\nБаллов: {total}/21\n"
            f"Последняя диагностика: {updated}\n"
            f"Статус: {premium}\n"
            f"📔 Записей в дневнике: {diary_n}"
        )
        if streak > 1:
            text += f"\n🔥 Дней подряд: {streak}"
        text += f"\n📋 Разборов: {analysis_n}\n"
        )
        test_results = db.get_test_results(callback.from_user.id, limit=5)
        if test_results:
            text += "\n**Последние тесты:**\n"
            names = {"bdi": "BDI", "bai": "BAI", "bhs": "BHS", "gad7": "GAD-7", "ptgi": "PTGI", "dass21": "DASS-21", "luscher": "Люшер"}
            for t in test_results:
                label = names.get(t["test_id"], t["test_id"])
                text += f"  {t['timestamp'][:10]}: {label} — {t['score']} баллов\n"
        if len(diag_log) > 1:
            text += "\n**История диагностик:**\n"
            for d in diag_log:
                e = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}.get(d['state'], '')
                text += f"  {d['timestamp'][:10]}: {e} {d['score']} баллов\n"
        text += "\nМожешь пройти диагностику заново в любой момент."
        buttons = [[InlineKeyboardButton(text="🔄 Пройти заново", callback_data="start_diagnosis")],
                   [InlineKeyboardButton(text="📋 Полная карта", callback_data="diag_card")]]
        if test_results:
            for t in reversed(test_results[-3:]):
                label = names.get(t["test_id"], t["test_id"])
                buttons.append([InlineKeyboardButton(text=f"📊 {t['timestamp'][:10]} {label} ({t['score']})", callback_data=f"tview_{t['id']}")])
        buttons.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "diag_card")
async def diagnostic_card(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user_data = db.get_user_state(uid)
    if not user_data or not user_data.get("state"):
        await callback.message.edit_text("Сначала пройди диагностику через /start.", reply_markup=back_to_menu_kb)
        await callback.answer()
        return
    total = user_data["score"] or 0
    emoji = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}
    level = "🔴 Кризис" if total >= 15 else ("🟡 Стабилизация" if total >= 7 else "🟢 Восстановление")
    bar = "🟥" * min(total, 21) + "⬜" * (21 - min(total, 21))
    premium = "⭐ Premium" if db.is_premium(uid) else "—"

    lines = [f"📋 **Диагностическая карта**\n"]
    lines.append(f"{emoji.get(user_data.get('state',''),'')} **{level}**")
    lines.append(f"`{bar}`  {total}/21 баллов")
    lines.append(f"Статус: {premium}\n")

    diag_log = db.get_diagnosis_log(uid, limit=10)
    if diag_log:
        lines.append("**📈 История диагностик:**")
        for d in diag_log:
            e = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}.get(d['state'], '')
            lines.append(f"{d['timestamp'][:10]}: {e} {d['state']} ({d['score']})")

    tests = db.get_test_results(uid, limit=10)
    if tests:
        lines.append("\n**📊 Результаты тестов:**")
        names = {"bdi": "BDI", "bai": "BAI", "bhs": "BHS", "gad7": "GAD-7", "ptgi": "PTGI", "dass21": "DASS-21", "luscher": "Люшер"}
        for t in tests:
            label = names.get(t["test_id"], t["test_id"])
            lines.append(f"{t['timestamp'][:10]}: {label} — {t['score']} баллов")

    analyses = db.get_all_analyses(uid, limit=5)
    if analyses:
        lines.append("\n**📋 Разборы:**")
        for a in analyses:
            e = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}.get(a['state'], '')
            lines.append(f"{a['timestamp'][:10]}: {e} {a['state']} ({a['score']})")

    lines.append(f"\n📔 Записей в дневнике: {db.get_diary_count(uid)}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
        ]), parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data == "my_analysis")
async def show_my_analysis(callback: types.CallbackQuery):
    analyses = db.get_all_analyses(callback.from_user.id, limit=20)
    if not analyses:
        await callback.message.edit_text(
            "У тебя пока нет сохранённых разборов. Пройди диагностику и ответь на вопросы, чтобы получить экспертный анализ.",
            reply_markup=back_to_menu_kb
        )
        await callback.answer()
        return
    text = "📋 **Мои разборы**\n\nНажми на разбор, чтобы открыть:\n"
    buttons = []
    for a in analyses:
        date = a["timestamp"][:10]
        em = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}.get(a["state"], "")
        buttons.append([InlineKeyboardButton(text=f"{em} {date} — {a['score']} баллов", callback_data=f"aview_{a['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("aview_"))
async def analysis_view(callback: types.CallbackQuery):
    aid = int(callback.data.split("_")[-1])
    a = db.get_analysis_by_id(aid, callback.from_user.id)
    if not a:
        await callback.answer("Разбор не найден.", show_alert=True)
        return
    state_name = a["state"].capitalize()
    text = (
        f"📋 **Разбор от {a['timestamp'][:10]}**\n"
        f"Состояние: **{state_name}** ({a['score']} баллов)\n\n"
        f"{a['analysis']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку разборов", callback_data="my_analysis")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("tview_"))
async def test_view(callback: types.CallbackQuery):
    tid = int(callback.data.split("_")[-1])
    t = db.get_test_result_by_id(tid, callback.from_user.id)
    if not t:
        await callback.answer("Результат не найден.", show_alert=True)
        return
    names = {"bdi": "BDI (депрессия)", "bai": "BAI (тревога)", "bhs": "BHS (безнадёжность)", "gad7": "GAD-7 (тревога)", "ptgi": "PTGI (посттравматический рост)", "dass21": "DASS-21 (депрессия/тревога/стресс)", "luscher": "Тест Люшера"}
    label = names.get(t["test_id"], t["test_id"])
    text = (
        f"📊 **{label}**\n"
        f"Дата: {t['timestamp'][:10]}\n"
        f"Результат: **{t['score']} баллов**\n"
    )
    if t["details"]:
        text += f"Интерпретация: {t['details']}\n"
    if t["test_id"] == "dass21" and t["details"]:
        for part in t["details"].split(", "):
            text += f"  • {part}\n"
    text += "\n⚠️ Это не диагноз. Тест показывает текущее состояние."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К состоянию", callback_data="my_state")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
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
        db.save_test_result(message.chat.id, "bdi", total, level)
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


# ===== TESTS MENU =====
_test_sessions = {}

def test_level(score, levels):
    for lo, hi, label in levels:
        if lo <= score <= hi:
            return label
    return levels[-1][2]

def tests_menu_kb():
    kb = [[InlineKeyboardButton(text="📋 Шкала депрессии Бека (BDI)", callback_data="beck_test")]]
    for k, v in TESTS_MENU.items():
        kb.append([InlineKeyboardButton(text=v["name"], callback_data=f"t_start_{k}")])
    kb.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


@dp.callback_query(F.data == "tests_menu")
async def tests_menu_handler(callback: types.CallbackQuery):
    text = "📋 **Тесты и опросники**\n\nВыбери тест. Результаты помогут лучше понять своё состояние."
    await callback.message.edit_text(text, reply_markup=tests_menu_kb(), parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("t_start_"))
async def start_test(callback: types.CallbackQuery):
    tid = callback.data[8:]

    if tid == "luscher":
        await start_luscher(callback)
        return

    test_map = {
        "bai": (_BAI_QUESTIONS, "sum", [(0, 7, "низкая тревога"), (8, 15, "лёгкая тревога"), (16, 25, "умеренная тревога"), (26, 63, "высокая тревога")]),
        "bhs": (_BHS_QUESTIONS, "bhs", [(0, 3, "минимальная безнадёжность"), (4, 8, "лёгкая"), (9, 14, "умеренная"), (15, 20, "тяжёлая безнадёжность")]),
        "gad7": (_GAD7_QUESTIONS, "sum", [(0, 4, "минимальная тревога"), (5, 9, "лёгкая"), (10, 14, "умеренная"), (15, 21, "высокая тревога")]),
        "ptgi": (_PTGI_QUESTIONS, "sum", [(0, 20, "низкий рост"), (21, 40, "умеренный"), (41, 63, "заметный"), (64, 105, "высокий посттравматический рост")]),
        "dass21": (_DASS21_QUESTIONS, "dass21", None),
    }
    qs, stype, levels = test_map[tid]
    _test_sessions[callback.from_user.id] = {"tid": tid, "q_index": 0, "answers": [], "total_q": len(qs), "qs": qs, "stype": stype, "levels": levels}
    await callback.answer()
    await show_test_question(callback.message, callback.from_user.id)


async def show_test_question(msg, uid):
    sess = _test_sessions.get(uid)
    if not sess:
        return
    qidx = sess["q_index"]
    qs = sess["qs"]
    if qidx >= sess["total_q"]:
        await finish_test(msg, uid)
        return

    if sess["tid"] == "bhs":
        text_q, is_rev = qs[qidx]
        opts = _BHS_OPTS
    else:
        text_q, opts = qs[qidx]

    text = f"**Вопрос {qidx+1}/{sess['total_q']}:** {text_q}\n\n"
    buttons = [[InlineKeyboardButton(text=opt, callback_data=f"t_ans_{i}")] for i, opt in enumerate(opts)]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("t_ans_"))
async def test_answer(callback: types.CallbackQuery):
    uid = callback.from_user.id
    val = int(callback.data.split("_")[-1])
    sess = _test_sessions.get(uid)
    if not sess:
        await callback.answer("Тест не найден. Начни заново.", show_alert=True)
        return

    # BHS: reverse scoring
    if sess["tid"] == "bhs":
        _, is_rev = sess["qs"][sess["q_index"]]
        val = 1 - val if is_rev else val

    sess["answers"].append(val)
    sess["q_index"] += 1
    await callback.answer()
    await show_test_question(callback.message, uid)


def compute_score(tid, answers):
    if tid == "bai":
        return sum(answers), None
    elif tid == "bhs":
        return sum(answers), None
    elif tid == "gad7":
        return sum(answers), None
    elif tid == "ptgi":
        return sum(answers), None
    elif tid == "dass21":
        d = sum(answers[i]*2 for i in range(21) if _DASS21_QUESTIONS[i][1] == "D")
        a = sum(answers[i]*2 for i in range(21) if _DASS21_QUESTIONS[i][1] == "A")
        s = sum(answers[i]*2 for i in range(21) if _DASS21_QUESTIONS[i][1] == "S")
        return None, {"D": d, "A": a, "S": s}
    return 0, None


def das_level(score, norms):
    for label, lo, hi in norms:
        if lo <= score <= hi:
            return label
    return norms[-1][0]

_DASS_NORMS = {
    "D": [("норма", 0, 9), ("лёгкая", 10, 13), ("умеренная", 14, 20), ("тяжёлая", 21, 27), ("очень тяжёлая", 28, 42)],
    "A": [("норма", 0, 7), ("лёгкая", 8, 9), ("умеренная", 10, 14), ("тяжёлая", 15, 19), ("очень тяжёлая", 20, 42)],
    "S": [("норма", 0, 14), ("лёгкая", 15, 18), ("умеренная", 19, 25), ("тяжёлая", 26, 33), ("очень тяжёлая", 34, 42)],
}

async def finish_test(msg, uid):
    sess = _test_sessions.pop(uid, None)
    if not sess:
        return
    score, sub = compute_score(sess["tid"], sess["answers"])

    if sess["tid"] == "dass21":
        d, a, s = sub["D"], sub["A"], sub["S"]
        dl = das_level(d, _DASS_NORMS["D"])
        al = das_level(a, _DASS_NORMS["A"])
        sl = das_level(s, _DASS_NORMS["S"])
        details = f"D:{d}({dl}), A:{a}({al}), S:{s}({sl})"
        db.save_test_result(msg.chat.id, "dass21", d + a + s, details)
        text = (
            f"📊 **DASS-21 завершён!**\n\n"
            f"**Депрессия (D):** {d} баллов — *{dl}*\n"
            f"  Вопросы: 3, 5, 10, 13, 16, 17, 21\n"
            f"  Норма: 0-9 | Лёгкая: 10-13 | Умеренная: 14-20 | Тяжёлая: 21+ | Оч. тяжёлая: 28+\n\n"
            f"**Тревога (A):** {a} баллов — *{al}*\n"
            f"  Вопросы: 2, 4, 7, 9, 15, 19, 20\n"
            f"  Норма: 0-7 | Лёгкая: 8-9 | Умеренная: 10-14 | Тяжёлая: 15+ | Оч. тяжёлая: 20+\n\n"
            f"**Стресс (S):** {s} баллов — *{sl}*\n"
            f"  Вопросы: 1, 6, 8, 11, 12, 14, 18\n"
            f"  Норма: 0-14 | Лёгкая: 15-18 | Умеренная: 19-25 | Тяжёлая: 26+ | Оч. тяжёлая: 34+\n\n"
            f"⚠️ Это скрининг, не диагноз. Результаты выше нормы — повод обратиться к специалисту."
        )
    else:
        level = test_level(score, sess["levels"])
        db.save_test_result(msg.chat.id, sess["tid"], score, level)
        text = (
            f"📋 **{TESTS_MENU[sess['tid']]['name']} завершён!**\n\n"
            f"Твой результат: **{score} баллов** — {level}.\n\n"
            "⚠️ Это не диагноз. Тест показывает текущее состояние."
        )
    await msg.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")


# ===== LUSCHER TEST =====
async def start_luscher(callback: types.CallbackQuery):
    _test_sessions[callback.from_user.id] = {"tid": "luscher", "round": 1, "step": 0, "picked": [], "order1": [], "order2": []}
    await callback.answer()
    await show_luscher_colors(callback.message, callback.from_user.id)


async def show_luscher_colors(msg, uid):
    sess = _test_sessions.get(uid)
    if not sess:
        return
    if sess["step"] >= len(LUSCHER_COLORS):
        # current round complete
        if sess["round"] == 1:
            sess["order1"] = sess["picked"][:]
            sess["round"] = 2
            sess["step"] = 0
            sess["picked"] = []
            import random
            shuffled = list(range(8))
            random.shuffle(shuffled)
            sess["shuffle"] = shuffled
            text = "🎨 **Тест Люшера — 2-й раунд**\n\nТеперь выбери цвета снова. Не старайся вспомнить предыдущий выбор — доверься первому впечатлению.\n\n"
            remaining = [(i, LUSCHER_COLORS[i][0], LUSCHER_COLORS[i][1]) for i in shuffled]
            buttons = [[InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"lusch_pick_{i}")] for i, emoji, name in remaining]
            await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
        else:
            await finish_luscher(msg, uid)
        return

    step = sess["step"]
    remaining = [(i, LUSCHER_COLORS[i][0], LUSCHER_COLORS[i][1]) for i in (range(8) if sess["round"] == 1 else sess.get("shuffle", range(8))) if i not in sess["picked"]]
    text = f"🎨 **Тест Люшера{' — 2-й раунд' if sess['round'] == 2 else ''}**\n\nВыбери **{step+1}-й** цвет (самый приятный из оставшихся):\n\n"
    if sess["picked"]:
        picked_str = ", ".join(f"{LUSCHER_COLORS[i][0]}({p+1})" for p, i in enumerate(sess["picked"]))
        text += f"Уже выбрано: {picked_str}\n\n"
    buttons = [[InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"lusch_pick_{i}")] for i, emoji, name in remaining]
    await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("lusch_pick_"))
async def luscher_pick(callback: types.CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split("_")[-1])
    sess = _test_sessions.get(uid)
    if not sess:
        await callback.answer("Тест не найден.", show_alert=True)
        return
    sess["picked"].append(idx)
    sess["step"] += 1
    await callback.answer()
    await show_luscher_colors(callback.message, uid)


async def finish_luscher(msg, uid):
    sess = _test_sessions.pop(uid, None)
    if not sess:
        return
    order1 = sess["order1"]
    order2 = sess["picked"]
    pos1 = {c: i for i, c in enumerate(order1)}
    pos2 = {c: i for i, c in enumerate(order2)}

    text = "🎨 **Тест Люшера завершён!**\n\n"
    text += "**1-й раунд:**\n"
    for i, c in enumerate(order1):
        text += f"  {i+1}. {LUSCHER_COLORS[c][0]} {LUSCHER_COLORS[c][1]}\n"
    text += "\n**2-й раунд:**\n"
    for i, c in enumerate(order2):
        text += f"  {i+1}. {LUSCHER_COLORS[c][0]} {LUSCHER_COLORS[c][1]}\n"

    text += "\n**Интерпретация:**\n"
    primary = {0, 1, 2, 3}
    stable = [c for c in range(8) if abs(pos1.get(c, 8) - pos2.get(c, 8)) <= 1]
    unstable = [c for c in range(8) if abs(pos1.get(c, 8) - pos2.get(c, 8)) >= 3]
    prim_first = sum(1 for c in range(4) if pos1.get(c, 8) < 4 and pos2.get(c, 8) < 4)
    prim_last = sum(1 for c in range(4) if pos1.get(c, 8) >= 4 and pos2.get(c, 8) >= 4)

    if prim_first >= 3:
        text += "✅ Основные цвета (красный, жёлтый, зелёный, синий) в начале в обоих раундах — эмоциональное равновесие.\n"
    elif prim_first >= 1:
        text += "⚠️ Часть основных цветов в начале — есть ресурс, но нестабильность.\n"
    else:
        text += "🔴 Основные цвета в конце в обоих раундах — возможен стресс или подавленность.\n"

    if len(stable) >= 5:
        text += "📌 Много стабильных выборов — у тебя есть устойчивые ценности и потребности.\n"
    elif len(stable) >= 3:
        text += "📌 Умеренная стабильность — часть потребностей осознана.\n"
    else:
        text += "📌 Мало стабильных выборов — возможна внутренняя растерянность.\n"

    if len(unstable) >= 3:
        text += "🔀 Значительные колебания между раундами — внутренний конфликт, неопределённость.\n"

    for c in stable:
        if c == 3:
            text += "🔵 Синий стабилен — потребность в покое и гармонии.\n"
        elif c == 0:
            text += "🔴 Красный стабилен — уверенность, активность.\n"
        elif c == 2:
            text += "🟢 Зелёный стабилен — потребность в самоутверждении.\n"
        elif c == 1:
            text += "🟡 Жёлтый стабилен — потребность в радости и развитии.\n"

    for c in unstable:
        if c == 7:
            text += "⬛ Чёрный нестабилен — борьба с отрицанием или страхом.\n"
        elif c == 4:
            text += "🟣 Фиолетовый нестабилен — колебания между чувствительностью и рациональностью.\n"
        elif c == 6:
            text += "⬜ Серый нестабилен — желание отгородиться vs потребность в контакте.\n"

    text += "\n*⚠️ Упрощённая трактовка. Полный тест Люшера проводится специалистом.*"

    stable_cnt = len(stable)
    summary_parts = []
    if prim_first >= 3:
        summary_parts.append("эмоциональное равновесие")
    elif prim_first >= 1:
        summary_parts.append("частичный ресурс, нестабильность")
    else:
        summary_parts.append("возможный стресс")

    if stable_cnt >= 5:
        summary_parts.append("устойчивые ценности")
    elif stable_cnt < 3:
        summary_parts.append("внутренняя растерянность")

    if len(unstable) >= 3:
        summary_parts.append("внутренний конфликт")
    if order1[0] == 2:
        summary_parts.append("потребность в стабильности")
    elif order1[0] == 0:
        summary_parts.append("потребность в действии")
    elif order1[0] == 3:
        summary_parts.append("потребность в покое")
    elif order1[0] == 1:
        summary_parts.append("потребность в радости")

    db.save_test_result(uid, "luscher", stable_cnt, ", ".join(summary_parts))
    await msg.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")


@dp.callback_query(F.data == "task")
async def show_task(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        text = "Сначала пройди диагностику. Нажми /start."
    else:
        state = user_data["state"]
        pool = list(TASKS.get(state, TASKS["стабилизация"]))
        tests = db.get_test_results(callback.from_user.id, limit=5)
        if tests:
            for t in tests:
                if t["test_id"] == "bai" and t["score"] >= 10:
                    pool.append("🌊 **Заземление:** Умойся холодной водой и сделай квадратное дыхание (4-4-4-4).")
                    pool.append("🧊 **Лёд:** Подержи кубик льда в руке 30 секунд, концентрируясь на ощущении.")
                if t["test_id"] == "bdi" and t["score"] >= 14:
                    pool.append("🌱 **Маленький шаг:** Сделай сегодня одно простое действие — заправь постель или выйди на 5 мин.")
                    pool.append("☀️ **Свет:** Посиди на солнце или у окна 10 минут, закрыв глаза.")
                if t["test_id"] == "gad7" and t["score"] >= 10:
                    pool.append("📝 **Выгрузи тревогу:** Напиши список «что меня тревожит» и раздели на контролируемое/неконтролируемое.")
                if t["test_id"] == "ptgi" and t["score"] < 21:
                    pool.append("💎 **Одна хорошая вещь:** Вспомни и запиши 1 качество, которое ты открыл(а) в себе после расставания.")
                if t["test_id"] == "bhs" and t["score"] >= 9:
                    pool.append("🌟 **Якорь будущего:** Представь себя через год — где ты, кто рядом, что чувствуешь. Запиши 3 детали.")
        chosen = random.choice(pool)
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


@dp.callback_query(F.data.startswith("diary_view_"))
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


@dp.message(StateFilter(None))
async def diary_entry(message: types.Message):
    await bot.send_chat_action(message.chat.id, action="typing")
    history = [e["entry"] for e in db.get_last_entries(message.from_user.id, limit=3)]
    username = message.from_user.first_name or message.from_user.username or ""
    last_date = db.get_last_diary_date(message.from_user.id)
    is_first_today = last_date != message.date.strftime("%Y-%m-%d")
    analysis = await ai_module.analyze_diary_entry(message.text, history=history, username=username, is_first_today=is_first_today, user_context=db.get_user_context(message.from_user.id))
    db.save_diary_entry(message.from_user.id, message.text, response=analysis)
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

_BAI_OPTS = ("Совсем нет", "Слабо", "Умеренно", "Сильно")
_BAI_QUESTIONS = [
    ("Онемение или покалывание", _BAI_OPTS),
    ("Ощущение жара", _BAI_OPTS),
    ("Неуверенная походка (дрожь в ногах)", _BAI_OPTS),
    ("Невозможность расслабиться", _BAI_OPTS),
    ("Страх, что случится самое плохое", _BAI_OPTS),
    ("Головокружение или потеря равновесия", _BAI_OPTS),
    ("Учащённое сердцебиение", _BAI_OPTS),
    ("Неустойчивость", _BAI_OPTS),
    ("Ужас или страх", _BAI_OPTS),
    ("Нервозность", _BAI_OPTS),
    ("Дрожь в руках", _BAI_OPTS),
    ("Ощущение удушья", _BAI_OPTS),
    ("Страх потерять контроль", _BAI_OPTS),
    ("Затруднённое дыхание", _BAI_OPTS),
    ("Страх умереть", _BAI_OPTS),
    ("Испуг", _BAI_OPTS),
    ("Расстройство желудка", _BAI_OPTS),
    ("Обмороки", _BAI_OPTS),
    ("Покраснение лица", _BAI_OPTS),
    ("Потливость (не связанная с жарой)", _BAI_OPTS),
    ("Ком в горле", _BAI_OPTS),
]

_BHS_OPTS = ("Нет", "Да")
# (question, is_reversed) — reversed means "Нет"=1, "Да"=0
_BHS_QUESTIONS = [
    ("Я жду будущего с надеждой и энтузиазмом", True),
    ("Мне лучше сдаться, потому что я ничего не могу изменить", False),
    ("Когда всё плохо, мне помогает мысль, что так будет не всегда", True),
    ("Я не могу представить, какой будет моя жизнь через 10 лет", False),
    ("У меня достаточно времени, чтобы осуществить свои планы", True),
    ("Я ожидаю, что у меня будет успех в том, что мне интересно", True),
    ("Будущее кажется мне тёмным", False),
    ("Я надеюсь, что в жизни у меня будет больше хорошего, чем у среднего человека", True),
    ("Мне не везёт, и нет причин ждать, что в будущем будет везти", False),
    ("Мой опыт научил меня, что всё к лучшему", True),
    ("Будущее, которое меня ждёт, кажется мне плохим", False),
    ("Я не думаю, что получу то, что действительно хочу", False),
    ("Когда я думаю о будущем, я чувствую, что буду счастливее, чем сейчас", True),
    ("Всё идёт не так, как надо", False),
    ("Я верю в своё светлое будущее", True),
    ("Я никогда не получаю то, чего хочу, поэтому глупо чего-то хотеть", False),
    ("Маловероятно, что я буду по-настоящему удовлетворён(а) в будущем", False),
    ("Будущее кажется мне расплывчатым и неопределённым", False),
    ("Я жду больше хорошего, чем плохого", True),
    ("Бесполезно добиваться того, что я хочу, потому что, скорее всего, я этого не получу", False),
]

_GAD7_OPTS = ("Совсем нет", "Несколько дней", "Более половины дней", "Почти каждый день")
_GAD7_QUESTIONS = [
    ("Нервозность, тревожность или ощущение «на взводе»", _GAD7_OPTS),
    ("Неспособность прекратить беспокоиться или контролировать тревогу", _GAD7_OPTS),
    ("Чрезмерное беспокойство по разным поводам", _GAD7_OPTS),
    ("Трудность расслабиться", _GAD7_OPTS),
    ("Такая неусидчивость, что трудно сидеть на месте", _GAD7_OPTS),
    ("Лёгкая раздражительность или вспыльчивость", _GAD7_OPTS),
    ("Чувство страха, будто вот-вот случится что-то ужасное", _GAD7_OPTS),
]

_PTGI_OPTS = ("Не было", "Очень слабо", "Слабо", "Умеренно", "Сильно", "Очень сильно")
_PTGI_QUESTIONS = [
    ("Я изменил(а) свои приоритеты в жизни", _PTGI_OPTS),
    ("Я стал(а) больше ценить собственную жизнь", _PTGI_OPTS),
    ("У меня появились новые интересы", _PTGI_OPTS),
    ("Я почувствовал(а) в себе больше силы", _PTGI_OPTS),
    ("Я стал(а) лучше понимать духовные вопросы", _PTGI_OPTS),
    ("Я яснее понял(а), на кого могу положиться", _PTGI_OPTS),
    ("Я выбрал(а) новый жизненный путь", _PTGI_OPTS),
    ("Я стал(а) более близким(ой) с людьми", _PTGI_OPTS),
    ("Я стал(а) более открыто выражать эмоции", _PTGI_OPTS),
    ("Я знаю, что могу справиться с трудностями", _PTGI_OPTS),
    ("Я могу делать свою жизнь лучше", _PTGI_OPTS),
    ("Я стал(а) лучше принимать ход событий", _PTGI_OPTS),
    ("Я могу лучше ценить каждый день", _PTGI_OPTS),
    ("У меня появились новые возможности", _PTGI_OPTS),
    ("У меня появилось больше сострадания к другим", _PTGI_OPTS),
    ("Я стал(а) больше вкладывать в отношения", _PTGI_OPTS),
    ("Я стал(а) больше стараться изменить то, что нужно", _PTGI_OPTS),
    ("Я стал(а) более религиозным/ой или духовным/ой", _PTGI_OPTS),
    ("Я обнаружил(а), что сильнее, чем думал(а)", _PTGI_OPTS),
    ("Я многое узнал(а) о том, на что способны люди", _PTGI_OPTS),
    ("Я стал(а) лучше принимать необходимость быть зависимым/ой", _PTGI_OPTS),
]

_DASS21_OPTS = ("Не подходит", "Отчасти", "Значительно", "Очень")
# (question, subscale) where subscale: D=depression, A=anxiety, S=stress
_DASS21_QUESTIONS = [
    ("Мне было трудно успокоиться", "S"),
    ("Я чувствовал(а) сухость во рту", "A"),
    ("Я не мог(ла) испытывать положительные эмоции", "D"),
    ("У меня были проблемы с дыханием", "A"),
    ("Мне было трудно начать действовать", "D"),
    ("Я реагировал(а) слишком остро", "S"),
    ("У меня была дрожь", "A"),
    ("Я тратил(а) много энергии на тревогу", "S"),
    ("Я боялся(лась) ситуаций, где могу запаниковать", "A"),
    ("Я чувствовал(а), что ждать не от чего", "D"),
    ("Я чувствовал(а) себя беспокойным(ой)", "S"),
    ("Мне было трудно расслабиться", "S"),
    ("Я чувствовал(а) уныние и подавленность", "D"),
    ("Я не мог(ла) терпеть то, что мешает делу", "S"),
    ("Я чувствовал(а) близость паники", "A"),
    ("Я ни к чему не мог(ла) проявить энтузиазм", "D"),
    ("Я чувствовал(а), что не представляю ценности", "D"),
    ("Я был(а) довольно обидчив(а)", "S"),
    ("Я чувствовал(а) изменение сердцебиения", "A"),
    ("Я чувствовал(а) страх без причины", "A"),
    ("Жизнь казалась мне бессмысленной", "D"),
]

TESTS_MENU = {
    "bai": {"name": "😰 Шкала тревоги Бека (BAI)", "desc": "21 вопрос о физических симптомах тревоги."},
    "bhs": {"name": "🌑 Шкала безнадёжности Бека (BHS)", "desc": "20 утверждений о вашем взгляде в будущее."},
    "gad7": {"name": "😟 GAD-7 (тревога)", "desc": "7 вопросов о тревоге за последние 2 недели."},
    "ptgi": {"name": "🌱 PTGI (посттравматический рост)", "desc": "21 вопрос — что изменилось после кризиса."},
    "dass21": {"name": "📊 DASS-21 (депрессия, тревога, стресс)", "desc": "21 вопрос, оценивает 3 шкалы."},
    "luscher": {"name": "🎨 Тест Люшера", "desc": "Выберите цвета в порядке предпочтения."},
}


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
    modes = list(cat["modes"].items())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lsc:det:{i}")]
            for i, (name, _) in enumerate(modes)
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in modes:
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "lib_schema_cop")
async def schema_cop(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["cop"]
    text = f"{cat['emoji']} **{cat['title']}**\n\n"
    modes = list(cat["modes"].items())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lsc:cop:{i}")]
            for i, (name, _) in enumerate(modes)
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in modes:
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "lib_schema_health")
async def schema_health(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["health"]
    text = f"{cat['emoji']} **{cat['title']}**\n\n"
    modes = list(cat["modes"].items())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lsc:health:{i}")]
            for i, (name, _) in enumerate(modes)
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in modes:
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("lsc:"))
async def schema_show_mode(callback: types.CallbackQuery):
    _, cat_key, idx = callback.data.split(":", 2)
    cat = SCHEMA_CATEGORIES.get(cat_key)
    if cat:
        modes = list(cat["modes"].items())
        idx = int(idx)
        if 0 <= idx < len(modes):
            mode_name, mode_desc = modes[idx]
            content = f"🧠 **{mode_name}**\n\n{mode_desc}"
            await callback.message.edit_text(
                content,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"lib_schema_{cat_key}")]
                ]), parse_mode="Markdown"
            )
            await callback.answer()
            return
    await callback.answer("Режим не найден.", show_alert=True)


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
