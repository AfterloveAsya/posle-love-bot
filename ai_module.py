import aiohttp
import logging
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-r1:free"

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
                    "Ты — бережный психолог-ассистент в схема-терапии. "
                    "Пользователь делится личными переживаниями после расставания. "
                    "Твоя задача: выделить 1-2 повторяющиеся эмоции или мысли (например, вина, обида, страх одиночества) "
                    "и мягко, без оценок, назвать их. Не давай советов, не предлагай решений, просто назови чувства, "
                    "которые ты заметил. Используй фразы вроде: «Мне слышится грусть и тоска по прошлому», "
                    "«В твоих словах есть много самокритики». "
                    "Заверши коротким поддерживающим предложением (не более 5 предложений всего)."
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
                    return f"❌ Ошибка API ({resp.status}): {error_text[:200]}"
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"AI analyze failed: {e}")
        return f"❌ Ошибка соединения: {e}"
