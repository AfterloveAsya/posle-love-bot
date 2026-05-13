import asyncio
import logging
from datetime import datetime
import random
from aiogram import Bot
import db

TASKS = {
    "кризис": [
        "🌊 «Холодная вода»: Умойся ледяной водой или подержи запястья под холодной струёй 30 секунд. Это снижает тревогу.",
        "🌳 «5-4-3-2-1»: Назови 5 вещей, которые видишь, 4 — которые можешь потрогать, 3 — слышишь, 2 — запаха, 1 — вкус.",
        "💨 «Квадратное дыхание»: Вдох на 4 счёта, задержка на 4, выдох на 4, задержка на 4. Повтори 3-5 раз.",
    ],
    "стабилизация": [
        "📖 «Письмо без отправки»: Напиши бывшему партнёру всё, что чувствуешь. Не отправляй.",
        "🌼 «Маленькая радость»: Запланируй сегодня что-то приятное для себя.",
        "🧘 «Сканирование тела»: Закрой глаза и мысленно пройди вниманием от макушки до пяток.",
    ],
    "восстановление": [
        "🎨 «Моё будущее»: Нарисуй или опиши, каким ты видишь своё идеальное утро через год.",
        "🌟 «Сильные стороны»: Напиши 5 своих качеств, которые помогли тебе пережить трудности.",
        "💎 «Уроки опыта»: Подумай, что важного ты узнал(а) о себе благодаря этим отношениям.",
    ]
}

MORNING_GREETINGS = [
    "🌅 Доброе утро! Новый день — это новый шаг к себе.",
    "☀️ С пробуждением! Помни, ты справляешься.",
    "🌿 Утро — время заботы о себе. Вот твоё задание на сегодня:",
]
EVENING_GREETINGS = [
    "🌙 Вечер — время тишины и рефлексии.",
    "✨ День подходит к концу. Загляни в дневник, если хочется.",
    "🕯️ Несколько минут для себя перед сном.",
]


async def scheduled_task(bot: Bot):
    logging.info("Scheduler started")
    last_sent = {}

    while True:
        now = datetime.utcnow()
        current_hour = now.hour
        current_date = now.date()

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, state FROM users")
        users = cursor.fetchall()
        conn.close()

        for user in users:
            user_id = user["user_id"]
            state = user["state"]
            settings = db.get_settings(user_id)
            mh = settings["morning_hour"]
            eh = settings["evening_hour"]

            key_m = f"morning_{user_id}"
            key_e = f"evening_{user_id}"

            try:
                if current_hour == mh and last_sent.get(key_m) != current_date:
                    greeting = random.choice(MORNING_GREETINGS)
                    tasks = TASKS.get(state, TASKS["стабилизация"])
                    task = random.choice(tasks)
                    text = f"{greeting}\n\n{task}"
                    await bot.send_message(user_id, text)
                    last_sent[key_m] = current_date

                if current_hour == eh and last_sent.get(key_e) != current_date:
                    greeting = random.choice(EVENING_GREETINGS)
                    text = f"{greeting}\n\n📓 Как прошёл твой день? Можешь написать мне — я сохраню запись в дневник."
                    await bot.send_message(user_id, text)
                    last_sent[key_e] = current_date
            except Exception as e:
                logging.error(f"Failed to send to {user_id}: {e}")
                continue

        await asyncio.sleep(60)
