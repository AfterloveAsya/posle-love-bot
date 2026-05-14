import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot
import db

MORNING_HOUR = 6
EVENING_HOUR = 18

TASKS = {
    "кризис": [
        "🌊 «Холодная вода»: Умойся ледяной водой или подержи запястья под холодной струёй 30 секунд.",
        "🌳 «5-4-3-2-1»: Назови 5 вещей, которые видишь, 4 — трогаешь, 3 — слышишь, 2 — запаха, 1 — вкус.",
        "💨 «Квадратное дыхание»: Вдох на 4 счёта, задержка на 4, выдох на 4, задержка на 4. 5 циклов.",
    ],
    "стабилизация": [
        "📖 «Письмо без отправки»: Напиши бывшему всё, что чувствуешь. Не отправляй.",
        "🌼 «Маленькая радость»: Сделай что-то приятное для себя осознанно.",
        "🧘 «Сканирование тела»: Мысленно пройди вниманием от макушки до пяток, расслабляя напряжение.",
    ],
    "восстановление": [
        "🎨 «Моё будущее»: Опиши своё идеальное утро через год — детали, чувства, окружение.",
        "🌟 «Сильные стороны»: Напиши 5 своих качеств, которые помогли тебе пройти через трудности.",
        "💎 «Уроки опыта»: Чему важному ты научился(ась) благодаря этим отношениям?",
    ],
}

MORNING_GREETINGS = [
    "🌅 Доброе утро! Новый день — новый шаг к себе.",
    "☀️ С пробуждением! Ты справляешься, даже если не верится.",
    "🌿 Утро — время заботы. Вот твоё сегодняшнее задание:",
]

EVENING_GREETINGS = [
    "🌙 Вечер — время тишины и рефлексии.",
    "✨ День завершается. Как он прошёл? Можешь написать мне.",
    "🕯️ Несколько минут для себя. Загляни в дневник.",
]


async def scheduled_task(bot: Bot):
    logging.info("Scheduler started")
    last_morning_sent = None
    last_evening_sent = None

    while True:
        now = datetime.utcnow()
        current_hour = now.hour
        current_date = now.date()

        if current_hour == MORNING_HOUR and last_morning_sent != current_date:
            logging.info("Running morning broadcast...")
            await broadcast(bot, "morning")
            last_morning_sent = current_date

        if current_hour == EVENING_HOUR and last_evening_sent != current_date:
            logging.info("Running evening broadcast...")
            await broadcast(bot, "evening")
            last_evening_sent = current_date

        await asyncio.sleep(60)


async def broadcast(bot: Bot, time_of_day: str):
    users = db.get_all_users_with_times()
    for user in users:
        user_id = user["user_id"]
        state = user["state"]
        try:
            if time_of_day == "morning":
                greeting = random.choice(MORNING_GREETINGS)
                tasks = TASKS.get(state, TASKS["стабилизация"])
                task = random.choice(tasks)
                text = f"{greeting}\n\n{task}"
            else:
                greeting = random.choice(EVENING_GREETINGS)
                text = f"{greeting}\n\n📓 Как прошёл твой день? Можешь написать мне — я сохраню запись в дневник."

            await bot.send_message(user_id, text)
        except Exception as e:
            logging.error(f"Failed to send to {user_id}: {e}")
            continue
