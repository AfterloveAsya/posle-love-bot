import aiohttp
import logging
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_DIARY = "openai/gpt-4o-mini"
MODEL_EXPERT = "deepseek/deepseek-chat"

DIARY_SYSTEM_PROMPT = (
    "Ты — психолог-консультант (гештальт + КПТ). Твоя задача — анализировать "
    "дневниковые записи человека после расставания.\n\n"
    "ФОРМАТ ОТВЕТА:\n"
    "- Начни с отражения чувств (1-2 предложения)\n"
    "- Затем выдели ключевой паттерн (мысль/эмоция/поведение)\n"
    "- Закончи вопросом для самоисследования\n"
    "- Используй **маркдаун** для структуры\n\n"
    "СТРУКТУРА ОТВЕТА:\n"
    "**Что я слышу:** [эмпатичное отражение]\n"
    "**Паттерн:** [КПТ/схема-анализ]\n"
    "**Вопрос для тебя:** [открытый вопрос]\n\n"
    "ПРАВИЛА:\n"
    "- Не здоровайся, если это не первое сообщение за сегодня\n"
    "- Не ставь диагнозы\n"
    "- При суицидальных мыслях напиши: «То, что ты чувствуешь, — очень тяжело. "
    "Пожалуйста, обратись к специалисту: 8 (800) 333-44-34»\n"
    "- Не пиши «как твой AI-психолог» — ты часть бота «После любви»\n"
    "- Не говори «я понимаю тебя» — скажи «то, что ты чувствуешь, — нормально»\n"
    "- Ответ: 2-4 предложения + вопрос, без воды"
)


async def analyze_diary_entry(text: str, history: list = None, username: str = "", is_first_today: bool = True, user_context: str = "") -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    system = DIARY_SYSTEM_PROMPT
    if user_context:
        system += f"\n\nКонтекст пользователя:\n{user_context}"
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
            {"role": "system", "content": [{"type": "text", "text": system}]},
            {"role": "user", "content": [{"type": "text", "text": user_content}]}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter diary error {resp.status}: {error_text}")
                    return "Пока не могу проанализировать запись, но я её сохранил."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"AI analyze failed: {e}")
        return "Пока не могу проанализировать запись, но я её сохранил."


async def expert_analysis(user_story: list, user_context: str = "") -> str:
    context = "\n".join([f"Вопрос: {item['q']}\nОтвет: {item['a']}" for item in user_story])
    system = (
        "Ты — схема-терапевт. Проанализируй историю клиента после расставания.\n\n"
        "ТВОЯ ЗАДАЧА:\n"
        "1. Определи ведущий дезадаптивный режим (строго один из списка):\n"
        "   - Уязвимый Ребёнок\n"
        "   - Карающий Родитель\n"
        "   - Отстранённый Защитник\n"
        "   - Разгневанный Защитник\n"
        "   - Режим «Спасатель»\n"
        "   - Перфекционист\n"
        "   - Преследователь\n"
        "   - Здоровый Взрослый\n\n"
        "2. Паттерн поведения: капитуляция / избегание / гиперкомпенсация\n\n"
        "3. Точка ближайшего развития (конкретное действие на эту неделю)\n\n"
        "ФОРМАТ ОТВЕТА:\n"
        "**🧠 Ведущий режим:** [название]\n"
        "**🔍 Паттерн:** [название]\n"
        "**📌 Что делать:** [конкретный шаг]\n\n"
        "**💬 Разбор:**\n"
        "[бережно, 2-3 абзаца]\n\n"
        "**🤝 Поддержка:**\n"
        "[короткая фраза]"
    )
    if user_context:
        system += f"\n\nКонтекст пользователя:\n{user_context}"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_EXPERT,
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": system}]},
            {"role": "user", "content": [{"type": "text", "text": f"История клиента:\n{context}"}]}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter expert error {resp.status}: {error_text}")
                    return "Не удалось провести экспертный анализ, но я сохраню твою историю."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Expert analysis failed: {e}")
        return "Не удалось провести экспертный анализ, но я сохраню твою историю."
