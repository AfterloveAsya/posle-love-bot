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
    LabeledPrice,
    PreCheckoutQuery,
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


main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Сегодняшнее задание", callback_data="task")],
        [InlineKeyboardButton(text="📓 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="📊 Моё состояние", callback_data="my_state")],
        [InlineKeyboardButton(text="🔍 Углублённый разбор", callback_data="deep_analysis")],
        [InlineKeyboardButton(text="📚 Библиотека техник", callback_data="library")],
        [InlineKeyboardButton(text="🆘 Кризисная помощь", callback_data="crisis")],
        [InlineKeyboardButton(text="⚙️ Подписка", callback_data="subscribe")],
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
    await callback.message.answer("Давай глубже. Расскажи, что произошло. Как давно вы расстались? Кто был инициатором?")
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
        text = "Ты ещё не проходил(а) диагностику. Нажми /start, чтобы начать."
    else:
        emoji = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢"}
        user_state = user_data["state"]
        score = user_data["score"]
        updated = user_data["updated_at"][:10]
        text = (
            f"{emoji.get(user_state, '')} Твоё состояние: **{user_state.capitalize()}**\n\n"
            f"Баллов: {score} (из 21)\n"
            f"Последняя диагностика: {updated}\n\n"
            "Ты можешь пройти диагностику заново — нажми /start."
        )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()


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
async def diary_prompt(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📓 Напиши мне сообщение — я проанализирую его через AI и сохраню в твой дневник.",
        reply_markup=back_to_menu_kb
    )
    await callback.answer()


@dp.message(StateFilter(None))
async def diary_entry(message: types.Message):
    await bot.send_chat_action(message.chat.id, action="typing")
    history = db.get_last_entries(message.from_user.id, limit=3)
    analysis = await ai_module.analyze_diary_entry(message.text, history=history)
    db.save_diary_entry(message.from_user.id, message.text)
    await message.answer(analysis, reply_markup=back_to_menu_kb)


# ===== SUBSCRIBE / STARS =====
@dp.callback_query(F.data == "subscribe")
async def subscribe_info(callback: types.CallbackQuery):
    if db.is_premium(callback.from_user.id):
        await callback.message.edit_text(
            "✅ У тебя активна Premium-подписка. Спасибо, что ты с нами!",
            reply_markup=back_to_menu_kb
        )
        await callback.answer()
        return

    prices = [
        LabeledPrice(label="Годовая подписка", amount=2990),
        LabeledPrice(label="Месячная подписка", amount=499),
    ]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Подписка «После любви»",
        description="Premium-доступ: персональные задания, AI-разбор, настройка времени.",
        payload="premium_subscription",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="premium",
    )
    await callback.answer()


@dp.pre_checkout_query()
async def checkout_process(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    if message.successful_payment.invoice_payload == "premium_subscription":
        amount = message.successful_payment.total_amount
        days = 365 if amount == 2990 else 30
        db.activate_premium(message.from_user.id, days)
        await message.answer("🎉 Твоя Premium-подписка активирована! Теперь тебе доступны все возможности.")


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
    "Уязвимый Ребёнок": (
        "Это часть нас, которая хранит боль, одиночество и потребность в заботе.\n\n"
        "🧸 **Как работать:**\n"
        "• Представь себя в детстве. Что бы ты хотел(а) услышать?\n"
        "• Напиши письмо себе-ребёнку со словами поддержки\n"
        "• Положи руку на сердце и скажи: «Я с тобой»"
    ),
    "Карающий Родитель": (
        "Внутренний критик, который ругает за ошибки и не даёт покоя.\n\n"
        "🎯 **Техника:**\n"
        "• Заметь его голос и скажи «Стоп»\n"
        "• Дай ему смешное имя (например, «Ворчун»)\n"
        "• Ответь ему с позиции взрослого: «Я делаю всё, что могу»"
    ),
    "Заземление": (
        "Практика возвращения в тело через 5 чувств.\n\n"
        "🌳 **5-4-3-2-1:**\n"
        "• 5 вещей, которые видишь\n"
        "• 4 — можешь потрогать\n"
        "• 3 — слышишь\n"
        "• 2 — запаха\n"
        "• 1 — вкус"
    ),
    "Управление триггерами": (
        "Триггер — стимул, вызывающий острую эмоциональную реакцию.\n\n"
        "📝 **Упражнение:**\n"
        "• Составь список своих триггеров\n"
        "• Для каждого придумай план безопасности\n"
        "• В момент триггера сначала дыши, потом действуй"
    ),
}


@dp.callback_query(F.data == "library")
async def library_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=name, callback_data=f"lib_{name}")] for name in LIBRARY.keys()]
        + [[InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]]
    )
    await callback.message.edit_text("📚 **Библиотека техник**\n\nВыбери тему:", reply_markup=kb, parse_mode="Markdown")
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
