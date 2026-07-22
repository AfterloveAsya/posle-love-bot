import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot
import db

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
    "здоров": [
        "🌱 «Мой рост»: Напиши 3 вещи, которые ты теперь знаешь о себе благодаря пройденному опыту.",
        "🗺️ «Карта желаний»: Опиши 3 цели на ближайшие полгода — от маленьких до больших.",
        "💞 «Благодарность»: Напиши, за что ты благодарен(на) этим отношениям. Без обесценивания.",
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
    last_sent = {}

    while True:
        now = datetime.utcnow()
        current_hour = now.hour
        current_date = now.date()
        users = db.get_all_users_with_times()

        for user in users:
            uid = user["user_id"]
            mh = user["morning_hour"]
            eh = user["evening_hour"]

            if current_hour == mh and last_sent.get(f"m_{uid}") != current_date:
                try:
                    state = user["state"]
                    greeting = random.choice(MORNING_GREETINGS)
                    tasks = TASKS.get(state, TASKS["стабилизация"])
                    task = random.choice(tasks)
                    await bot.send_message(uid, f"{greeting}\n\n{task}")
                    last_sent[f"m_{uid}"] = current_date
                except Exception as e:
                    logging.error(f"Morning broadcast failed for {uid}: {e}")

            if current_hour == eh and last_sent.get(f"e_{uid}") != current_date:
                try:
                    greeting = random.choice(EVENING_GREETINGS)
                    text = f"{greeting}\n\n📓 Как прошёл твой день? Можешь написать мне — я сохраню запись в дневник."
                    await bot.send_message(uid, text)
                    last_sent[f"e_{uid}"] = current_date
                except Exception as e:
                    logging.error(f"Evening broadcast failed for {uid}: {e}")

        await asyncio.sleep(60)
