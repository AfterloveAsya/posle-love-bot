import asyncio
import logging
from datetime import datetime
import random
from aiogram import Bot
import db

TASKS = {
    "кризис": [
        "🌊 «Холодная вода»: Умойся ледяной водой или подержи запястья под холодной струёй 30 секунд.",
        "🌳 «5-4-3-2-1»: Назови 5 вещей, 4 — потрогать, 3 — услышать, 2 — запаха, 1 — вкус.",
        "💨 «Квадратное дыхание»: Вдох на 4 — задержка 4 — выдох 4 — задержка 4.",
    ],
    "стабилизация": [
        "📖 «Письмо без отправки»: Напиши всё, что чувствуешь. Не отправляй.",
        "🌼 «Маленькая радость»: Запланируй сегодня что-то приятное для себя.",
        "🧘 «Сканирование тела»: Пройди вниманием от макушки до пяток.",
    ],
    "восстановление": [
        "🎨 «Моё будущее»: Опиши своё идеальное утро через год.",
        "🌟 «Сильные стороны»: Напиши 5 качеств, которые помогли тебе.",
        "💎 «Уроки опыта»: Что важного ты узнал(а) о себе?",
    ]
}

MORNING_GREETINGS = [
    "🌅 Доброе утро! Новый день — новый шаг к себе.",
    "☀️ С пробуждением! Помни, ты справляешься.",
    "🌿 Утро — время заботы о себе. Вот задание на сегодня:",
]
EVENING_GREETINGS = [
    "🌙 Вечер — время тишины и рефлексии.",
    "✨ День подходит к концу. Загляни в дневник.",
    "🕯️ Несколько минут для себя перед сном.",
]


async def scheduled_task(bot: Bot):
    logging.info("Scheduler started")
    last_sent = {}

    while True:
        now = datetime.utcnow()
        current_hour = now.hour
        current_date = now.date()

        users = db.get_all_users_with_times()

        for user in users:
            user_id = user["user_id"]
            state = user["state"]
            mh = user["morning_hour"]
            eh = user["evening_hour"]

            key_m = f"morning_{user_id}"
            key_e = f"evening_{user_id}"

            try:
                if current_hour == mh and last_sent.get(key_m) != current_date:
                    greeting = random.choice(MORNING_GREETINGS)
                    tasks = TASKS.get(state, TASKS["стабилизация"])
                    task = random.choice(tasks)
                    await bot.send_message(user_id, f"{greeting}\n\n{task}")
                    last_sent[key_m] = current_date

                if current_hour == eh and last_sent.get(key_e) != current_date:
                    greeting = random.choice(EVENING_GREETINGS)
                    await bot.send_message(user_id, f"{greeting}\n\n📓 Как прошёл твой день? Напиши мне — я сохраню запись в дневник.")
                    last_sent[key_e] = current_date
            except Exception as e:
                logging.error(f"Failed to send to {user_id}: {e}")
                continue

        await asyncio.sleep(60)
