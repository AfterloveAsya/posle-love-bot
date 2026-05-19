from aiogram import Router, types, F
from keyboards import back_to_menu_kb, schema_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

LIBRARY = {
    "Заземление": (
        "Техники, которые возвращают в «здесь и сейчас» при тревоге:\n\n"
        "🌳 **5-4-3-2-1:** Назови 5 вещей, 4 — потрогать, 3 — услышать, 2 — запаха, 1 — вкус.\n\n"
        "💨 **Квадратное дыхание:** Вдох на 4 — задержка на 4 — выдох на 4 — задержка на 4.\n\n"
        "🧊 **Холодная вода:** Умойся или подержи запястья под холодной водой 30 сек.\n\n"
        "👁 **Фиксация взгляда:** Рассматривай предмет 2 минуты, замечая детали."
    ),
    "Мысли и чувства": (
        "💭 **Работа с мыслями и чувствами**\n\n"
        "📓 **Дневник мыслей:** Записывай ситуацию → мысль → эмоцию → реакцию.\n\n"
        "✉️ **Письмо без отправки:** Напиши человеку всё, что чувствуешь. Не отправляй.\n\n"
        "🔄 **Смена перспективы:** «Что бы я сказал(а) другу в такой ситуации?»\n\n"
        "💬 **Аффирмации:** «Я имею право на свои чувства», «Я ценен/ценна сам(а) по себе»."
    ),
    "Управление триггерами": (
        "Триггер — стимул, вызывающий острую эмоциональную реакцию (напоминание о бывшем, "
        "место, запах, дата).\n\n"
        "📝 **Упражнение:**\n"
        "• Составь список своих триггеров\n"
        "• Для каждого придумай план безопасности\n"
        "• В момент триггера сначала дыши, потом действуй\n\n"
        "💡 **Помни:** триггер — это не опасность, это сигнал. Ты в безопасности сейчас."
    ),
}

SCHEMA_CATEGORIES = {
    "det": {
        "emoji": "",
        "title": "Детские и уязвимые режимы (раненые части)",
        "modes": {
            "Уязвимый ребёнок": "напуганный, покинутый, жаждущий любви и принятия. Чувствует себя никому не нужным, плачет, обижается, боится отвержения и одиночества.",
            "Режим «Жертва»": "ощущение беспомощности, бессилия перед обстоятельствами. Человек верит, что от него ничего не зависит, и пассивно страдает.",
        }
    },
    "cop": {
        "emoji": "",
        "title": "Дезадаптивные копинг-режимы (защитные механизмы, которые вредят)",
        "modes": {
            "Разгневанный защитник": "агрессивная, контролирующая часть. Нападает на других (кричит, обвиняет, ставит ультиматумы) или защищается через злость, когда границы нарушены.",
            "Отстранённый защитник": "убегает от боли через алкоголь, наркотики, азартные игры, порно, онанизм, залипание в сериалах или соцсетях. Отключает чувства, но не решает проблему.",
            "Режим «Спасатель»": "бросается решать чужие проблемы, жертвует собой, помогает даже в ущерб себе. Делает это из тревоги и страха быть ненужным (в отличие от здоровой заботы).",
            "Режим «Ищущий одобрение» (Угодник)": "подстраивается под других, боится сказать «нет», постоянно нуждается в похвале и признании, чтобы чувствовать себя ценным.",
            "Режим «Перфекционист»": "требует от себя идеальности во всём, иначе считает себя «недостаточно хорошим». Приводит к выгоранию, тревоге и самобичеванию при ошибках.",
            "Режим «Преследователь»": "холодно и расчётливо обвиняет, манипулирует, требует справедливости. Может быть направлен на других или на себя. Отличается от Разгневанного защитника отсутствием горячности, более рационален.",
            "Карающий родитель": "внутренний критик, который стыдит, обесценивает, наказывает («ты никчёмный», «сам виноват», «не достоин любви»). Голос значимых взрослых из детства.",
        }
    },
    "health": {
        "emoji": "",
        "title": "Здоровые режимы",
        "modes": {
            "Здоровый взрослый": "сильная, осознанная часть, которая заботится о себе и внутреннем ребёнке, планирует, работает, ставит границы, анализирует свои режимы и управляет ими. Умеет и любить, и требовать, и отдыхать, не впадая в крайности.",
            "Счастливый ребёнок": "спонтанная, радостная часть, способная играть, творить, смеяться, получать удовольствие от простых вещей без чувства вины.",
        }
    },
}


@router.callback_query(F.data == "library")
async def library_menu(callback: types.CallbackQuery):
    lib_buttons = [[InlineKeyboardButton(text=name, callback_data=f"lib_{name}")] for name in LIBRARY.keys()]
    lib_buttons.append([InlineKeyboardButton(text="🧠 Схематерапия: режимы", callback_data="lib_schema")])
    lib_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=lib_buttons)
    await callback.message.edit_text("📚 **Библиотека техник**\n\nВыбери тему:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "lib_schema")
async def schema_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🧠 **Схематерапия: режимы**\n\n"
        "В схема-терапии выделяют три группы режимов — состояний, в которых мы можем находиться. "
        "Выбери группу, чтобы изучить каждый режим.",
        reply_markup=schema_menu_kb(), parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "lib_schema_det")
async def schema_det(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["det"]
    text = f"**{cat['title']}**\n\n"
    modes = list(cat["modes"].items())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lsc:det:{i}")]
            for i, (name, _) in enumerate(modes)
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in modes:
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "lib_schema_cop")
async def schema_cop(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["cop"]
    text = f"**{cat['title']}**\n\n"
    modes = list(cat["modes"].items())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lsc:cop:{i}")]
            for i, (name, _) in enumerate(modes)
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in modes:
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "lib_schema_health")
async def schema_health(callback: types.CallbackQuery):
    cat = SCHEMA_CATEGORIES["health"]
    text = f"**{cat['title']}**\n\n"
    modes = list(cat["modes"].items())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lsc:health:{i}")]
            for i, (name, _) in enumerate(modes)
        ] + [[InlineKeyboardButton(text="🔙 К группам", callback_data="lib_schema")]]
    )
    for name, desc in modes:
        text += f"**{name}** — {desc}\n\n"
    await callback.message.edit_text(text.strip(), reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("lsc:"))
async def schema_show_mode(callback: types.CallbackQuery):
    _, cat_key, idx = callback.data.split(":", 2)
    cat = SCHEMA_CATEGORIES.get(cat_key)
    if cat:
        modes = list(cat["modes"].items())
        idx = int(idx)
        if 0 <= idx < len(modes):
            mode_name, mode_desc = modes[idx]
            content = f"🧠 **{mode_name}**\n\n{mode_desc}"
            await callback.message.edit_text(
                content,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"lib_schema_{cat_key}")]
                ]), parse_mode="Markdown"
            )
            await callback.answer()
            return
    await callback.answer("Режим не найден.", show_alert=True)


@router.callback_query(F.data.startswith("lib_"))
async def show_library_article(callback: types.CallbackQuery):
    topic = callback.data[4:]
    content = LIBRARY.get(topic, "Скоро здесь будет подробная статья.")
    await callback.message.edit_text(f"📖 **{topic}**\n\n{content}", reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()
