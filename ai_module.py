import asyncio
import aiohttp
import logging
import os
import re

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_DIARY = "openai/gpt-4o"
MODEL_EXPERT = "deepseek/deepseek-chat"

DIARY_SYSTEM_PROMPT = (
    "Ты — опытный психотерапевт с 15-летним стажем, специализирующийся на "
    "работе с расставанием и утратой. Твои ответы — это живая речь "
    "профессионала, который бережно и с глубоким пониманием откликается "
    "на состояние клиента.\n\n"
    "КАК ТЫ ГОВОРИШЬ:\n"
    "- Естественно и тепло, без шаблонов и заготовок\n"
    "- Как в реальной терапии — сначала отзовись на чувства, "
    "чтобы человек почувствовал, что его слышат\n"
    "- Затем аккуратно подсвети то, что замечаешь (паттерн, "
    "повторяющийся сценарий, связь)\n"
    "- Заверши открытым вопросом, который продвигает исследование\n"
    "- Используй **полужирный** только для 1-2 ключевых слов, "
    "не для всей структуры\n\n"
    "ЧЕГО ИЗБЕГАТЬ:\n"
    "- Никаких «Что я слышу», «Паттерн», «Вопрос для тебя» как заголовков\n"
    "- Не ставь диагнозы и не навешивай ярлыки\n"
    "- Не говори «я понимаю тебя» — лучше: «то, что ты описываешь, — "
    "знакомое многим состояние»\n"
    "- Не пиши «как твой AI-психолог» — ты часть бота «После любви»\n"
    "- Если это не первое сообщение за сегодня — не здоровайся и не представляйся\n\n"
    "ДЛИНА ОТВЕТА:\n"
    "3-5 предложений + короткий бережный вопрос в конце. "
    "Без воды, но с ощущением присутствия.\n\n"
    "ПРИ СУИЦИДАЛЬНЫХ МЫСЛЯХ:\n"
    "«То, что ты чувствуешь, — очень тяжело. "
    "Пожалуйста, обратись к специалисту: 8 (800) 333-44-34»"
)


async def analyze_diary_entry(text: str, history: list = None, username: str = "", is_first_today: bool = True, user_context: str = "") -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://posle-love-bot.ru",
        "X-Title": "После любви"
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
            {"role": "system", "content": system},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7,
        "max_tokens": 600,
        "provider": {"order": ["OpenAI"], "allow_fallbacks": false}
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter diary error {resp.status} model={MODEL_DIARY}: {error_text[:500]}")
                    return "Пока не могу проанализировать запись, но я её сохранил."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except asyncio.TimeoutError:
        logging.error("OpenRouter diary timeout")
        return "Пока не могу проанализировать запись, но я её сохранил."
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
        "Content-Type": "application/json",
        "HTTP-Referer": "https://posle-love-bot.ru",
        "X-Title": "После любви"
    }
    payload = {
        "model": MODEL_EXPERT,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"История клиента:\n{context}"}
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


def parse_expert_response(response: str) -> dict:
    mode = pattern = advice = ""
    m = re.search(r'\*\*[🧠*]*\s*Ведущий режим:\*\*\s*(.*?)(?:\n|$)', response)
    if m: mode = m.group(1).strip()
    m = re.search(r'\*\*[🔍*]*\s*Паттерн:\*\*\s*(.*?)(?:\n|$)', response)
    if m: pattern = m.group(1).strip()
    m = re.search(r'\*\*[📌*]*\s*Что делать:\*\*\s*(.*?)(?:\n|$)', response)
    if m: advice = m.group(1).strip()
    return {"mode": mode, "pattern": pattern, "advice": advice}


DIALOG_SYSTEM_PROMPT = (
    "Ты — опытный психотерапевт, специализирующийся на работе с расставанием и утратой. "
    "Ты уже провёл(а) с клиентом диагностику и знаешь его контекст. "
    "Сейчас вы находитесь в свободном диалоге — клиент задаёт вопросы или делится тем, что приходит. "
    "Твоя задача:\n"
    "- Продолжать диалог естественно и бережно\n"
    "- Опираться на известный контекст (состояние, режим, тесты)\n"
    "- Давать конкретные, практичные советы\n"
    "- Задавать уточняющие вопросы, чтобы углублять понимание\n"
    "- Использовать русский язык, говорить тепло, но профессионально\n\n"
    "ВАЖНО:\n"
    "- Не повторяй разбор заново — ты уже его сделал(а)\n"
    "- Отвечай на то, что клиент сказал сейчас\n"
    "- Если клиент спрашивает про прошлый анализ — поясняй, а не копируй\n"
    "- Длина ответа: 2-5 предложений + вопрос\n"
    "- Не пиши «как твой AI-психолог» — ты часть бота «После любви»"
)


async def premium_dialog(user_message: str, user_context: str, history: list) -> str:
    system = DIALOG_SYSTEM_PROMPT
    if user_context:
        system += f"\n\nКОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:\n{user_context}"
    messages = [{"role": "system", "content": system}]
    for msg in history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://posle-love-bot.ru",
        "X-Title": "После любви"
    }
    payload = {
        "model": MODEL_EXPERT,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 600
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"OpenRouter dialog error {resp.status}: {error_text[:300]}")
                    return "Не могу ответить. Попробуй ещё раз."
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Dialog failed: {e}")
        return "Не могу ответить. Попробуй ещё раз."
