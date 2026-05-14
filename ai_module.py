import aiohttp
import logging
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"


async def analyze_diary_entry(text: str, history: list = None) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — бережный психолог-ассистент. Пользователь делится переживаниями. "
                    "Выдели 1-2 главные эмоции и назови их мягко, без оценок. Не давай советов. "
                    "Заверши короткой поддержкой. Пиши только на русском языке. Не более 5 предложений."
                )
            },
            {"role": "user", "content": text}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=20) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter error {resp.status}: {error_text}")
                    return "Пока не могу проанализировать запись, но я её сохранил."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"AI analyze failed: {e}")
        return "Пока не могу проанализировать запись, но я её сохранил."


async def expert_analysis(user_story: list) -> str:
    context = "\n".join([f"Вопрос: {item['q']}\nОтвет: {item['a']}" for item in user_story])
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — опытный схема-терапевт. Проанализируй историю клиента после расставания. "
                    "На основе ответов определи:\n"
                    "1. Ведущий дезадаптивный режим (Карающий Родитель, Уязвимый Ребёнок, Сердитый Ребёнок, Избегающий Защитник и т.д.).\n"
                    "2. Основной паттерн поведения (капитуляция, избегание, гиперкомпенсация).\n"
                    "3. Точку ближайшего развития — что клиенту важно сделать в первую очередь (например, заметить критикующий голос и дать ему имя).\n\n"
                    "Напиши это бережно, понятным языком, без директив, но с ясной структурой. Добавь короткое поддерживающее предложение."
                )
            },
            {"role": "user", "content": f"История клиента:\n{context}"}
        ],
        "temperature": 0.7,
        "max_tokens": 400
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=25) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter error {resp.status}: {error_text}")
                    return "Не удалось провести экспертный анализ, но я сохраню твою историю."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Expert analysis failed: {e}")
        return "Не удалось провести экспертный анализ, но я сохраню твою историю."
