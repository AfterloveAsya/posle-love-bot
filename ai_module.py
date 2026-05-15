import aiohttp
import logging
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_DIARY = "openai/gpt-4o-mini"
MODEL_EXPERT = "deepseek/deepseek-chat"

DIARY_SYSTEM_PROMPT = (
    "Ты опытный психолог-консультант, специализирующийся на гештальт-терапии и "
    "когнитивно-поведенческой терапии (КПТ). Твоя роль — предоставлять эмоциональную "
    "поддержку, помогать людям разобраться в своих чувствах и найти конструктивные "
    "способы решения проблем.\n\n"
    "ПРИНЦИПЫ РАБОТЫ:\n\n"
    "1. ГЕШТАЛЬТ-ТЕРАПИЯ:\n"
    "   - Фокусируйся на «здесь и сейчас»\n"
    "   - Помогай клиенту осознавать свои чувства и телесные ощущения\n"
    "   - Задавай вопросы типа: «Что ты чувствуешь прямо сейчас?», "
    "«Где в теле ты это ощущаешь?»\n\n"
    "2. КОГНИТИВНО-ПОВЕДЕНЧЕСКАЯ ТЕРАПИЯ:\n"
    "   - Помогай выявлять деструктивные мыслительные паттерны\n"
    "   - Исследуй связь между мыслями, чувствами и поведением\n"
    "   - Предлагай альтернативные способы мышления\n\n"
    "3. СТИЛЬ ОБЩЕНИЯ:\n"
    "   - Проявляй эмпатию и безоценочное принятие\n"
    "   - Используй активное слушание и отражение чувств\n"
    "   - Задавай открытые вопросы, способствующие самоисследованию\n"
    "   - Поддерживай тёплый, профессиональный тон\n\n"
    "4. ЭТИЧЕСКИЕ ПРИНЦИПЫ:\n"
    "   - Не диагностируй психические расстройства\n"
    "   - При серьёзных проблемах рекомендуй обращение к специалисту\n"
    "   - Признавай ограничения AI-консультирования\n\n"
    "ВАЖНО:\n"
    "- Отвечай на русском языке\n"
    "- Ответы должны быть 200-400 слов\n"
    "- При суицидальных мыслях немедленно рекомендуй обратиться к специалисту\n"
    "- Помни: твоя цель — помочь развить навыки самопомощи и самопонимания"
)


async def analyze_diary_entry(text: str, history: list = None, username: str = "", is_first_today: bool = True) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    parts = []
    if history:
        history_lines = "\n".join(f"- {h}" for h in history if isinstance(h, str))
        if history_lines:
            parts.append(f"Предыдущие записи клиента:\n{history_lines}")
    parts.append(text)
    user_content = "\n\n".join(parts)
    if username:
        user_content += f"\n\nКлиента зовут {username}."
    if not is_first_today:
        user_content += "\n\nВажно: это не первое сообщение за сегодня. Не здоровайся и не представляйся — просто продолжи анализ."
    payload = {
        "model": MODEL_DIARY,
        "messages": [
            {"role": "system", "content": DIARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=25) as resp:
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
        "model": MODEL_EXPERT,
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
        "max_tokens": 1000
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter error {resp.status}: {error_text}")
                    return "Не удалось провести экспертный анализ, но я сохраню твою историю."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Expert analysis failed: {e}")
        return "Не удалось провести экспертный анализ, но я сохраню твою историю."
