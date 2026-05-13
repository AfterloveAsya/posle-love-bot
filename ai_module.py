import aiohttp
import logging
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"

async def analyze_diary_entry(text: str) -> str:
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
                    "Ты — бережный психолог-ассистент. Пользователь делится переживаниями после расставания. "
                    "Выдели 1-2 главные эмоции и назови их мягко, без оценок. Не давай советов. "
                    "Заверши короткой поддержкой. Пиши только на русском языке. Не более 5 предложений."
                )
            },
            {
                "role": "user",
                "content": text
            }
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
                    return f"❌ Ошибка API ({resp.status})"
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"AI analyze failed: {e}")
        return "❌ Ошибка соединения"
