import random
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import BeckTest
import db
from test_data import (
    LUSCHER_COLORS, BECK_QUESTIONS, _BAI_QUESTIONS, _BHS_QUESTIONS,
    _BHS_OPTS, _GAD7_QUESTIONS, _PTGI_QUESTIONS, _DASS21_QUESTIONS,
    _DASS21_OPTS, _DASS_NORMS, TESTS_MENU, test_level, compute_score, das_level
)
from keyboards import back_to_menu_kb, tests_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
_test_sessions = {}


# ===== BECK TEST =====
@router.callback_query(F.data == "beck_test")
async def beck_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(beck_index=0, beck_score=0)
    await state.set_state(BeckTest.waiting_answer)
    await callback.answer()
    await ask_beck_question(callback.message, state, is_new_message=True)


async def ask_beck_question(message: types.Message, state: FSMContext, is_new_message: bool = False):
    data = await state.get_data()
    index = data.get("beck_index", 0)

    if index >= len(BECK_QUESTIONS):
        total = data.get("beck_score", 0)
        if total <= 13:
            level = "минимальный уровень депрессии"
        elif total <= 19:
            level = "лёгкая депрессия"
        elif total <= 28:
            level = "умеренная депрессия"
        else:
            level = "тяжёлая депрессия"
        text = (
            f"📋 **Тест Бека завершён!**\n\n"
            f"Твой результат: **{total} баллов** — {level}.\n\n"
            "⚠️ Это не диагноз. Тест показывает текущее эмоциональное состояние.\n"
            "Если тебя беспокоит результат — обратись к специалисту."
        )
        db.save_test_result(message.chat.id, "bdi", total, level)
        await message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
        await state.clear()
        return

    topic, options = BECK_QUESTIONS[index]
    text = f"**Вопрос {index+1}/21:** {topic}\n\n"
    buttons = []
    for i, opt in enumerate(options):
        buttons.append([InlineKeyboardButton(text=opt, callback_data=f"beck_a_{i}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if is_new_message:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("beck_a_"))
async def beck_answer(callback: types.CallbackQuery, state: FSMContext):
    answer = int(callback.data.split("_")[-1])
    data = await state.get_data()
    new_score = data.get("beck_score", 0) + answer
    new_index = data.get("beck_index", 0) + 1
    await state.update_data(beck_score=new_score, beck_index=new_index)
    await callback.answer()
    await ask_beck_question(callback.message, state)


# ===== TESTS MENU =====
@router.callback_query(F.data == "tests_menu")
async def tests_menu_handler(callback: types.CallbackQuery):
    text = "📋 **Тесты и опросники**\n\nВыбери тест. Результаты помогут лучше понять своё состояние."
    await callback.message.edit_text(text, reply_markup=tests_menu_kb(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("t_start_"))
async def start_test(callback: types.CallbackQuery):
    tid = callback.data[8:]

    if tid == "luscher":
        await start_luscher(callback)
        return

    test_map = {
        "bai": (_BAI_QUESTIONS, "sum", [(0, 7, "низкая тревога"), (8, 15, "лёгкая тревога"), (16, 25, "умеренная тревога"), (26, 63, "высокая тревога")]),
        "bhs": (_BHS_QUESTIONS, "bhs", [(0, 3, "минимальная безнадёжность"), (4, 8, "лёгкая"), (9, 14, "умеренная"), (15, 20, "тяжёлая безнадёжность")]),
        "gad7": (_GAD7_QUESTIONS, "sum", [(0, 4, "минимальная тревога"), (5, 9, "лёгкая"), (10, 14, "умеренная"), (15, 21, "высокая тревога")]),
        "ptgi": (_PTGI_QUESTIONS, "sum", [(0, 20, "низкий рост"), (21, 40, "умеренный"), (41, 63, "заметный"), (64, 105, "высокий посттравматический рост")]),
        "dass21": (_DASS21_QUESTIONS, "dass21", None),
    }
    qs, stype, levels = test_map[tid]
    _test_sessions[callback.from_user.id] = {"tid": tid, "q_index": 0, "answers": [], "total_q": len(qs), "qs": qs, "stype": stype, "levels": levels}
    await callback.answer()
    await show_test_question(callback.message, callback.from_user.id)


async def show_test_question(msg, uid):
    sess = _test_sessions.get(uid)
    if not sess:
        return
    qidx = sess["q_index"]
    qs = sess["qs"]
    if qidx >= sess["total_q"]:
        await finish_test(msg, uid)
        return

    if sess["tid"] == "bhs":
        text_q, is_rev = qs[qidx]
        opts = _BHS_OPTS
    elif sess["tid"] == "dass21":
        text_q, _ = qs[qidx]
        opts = _DASS21_OPTS
    else:
        text_q, opts = qs[qidx]

    text = f"**Вопрос {qidx+1}/{sess['total_q']}:** {text_q}\n\n"
    buttons = [[InlineKeyboardButton(text=opt, callback_data=f"t_ans_{i}")] for i, opt in enumerate(opts)]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("t_ans_"))
async def test_answer(callback: types.CallbackQuery):
    uid = callback.from_user.id
    val = int(callback.data.split("_")[-1])
    sess = _test_sessions.get(uid)
    if not sess:
        await callback.answer("Тест не найден. Начни заново.", show_alert=True)
        return

    if sess["tid"] == "bhs":
        _, is_rev = sess["qs"][sess["q_index"]]
        val = 1 - val if is_rev else val

    sess["answers"].append(val)
    sess["q_index"] += 1
    await callback.answer()
    await show_test_question(callback.message, uid)


async def finish_test(msg, uid):
    sess = _test_sessions.pop(uid, None)
    if not sess:
        return
    score, sub = compute_score(sess["tid"], sess["answers"])

    if sess["tid"] == "dass21":
        d, a, s = sub["D"], sub["A"], sub["S"]
        dl = das_level(d, _DASS_NORMS["D"])
        al = das_level(a, _DASS_NORMS["A"])
        sl = das_level(s, _DASS_NORMS["S"])
        details = f"D:{d}({dl}), A:{a}({al}), S:{s}({sl})"
        db.save_test_result(msg.chat.id, "dass21", d + a + s, details)
        text = (
            f"📊 **DASS-21 завершён!**\n\n"
            f"**Депрессия (D):** {d} баллов — *{dl}*\n"
            f"  Вопросы: 3, 5, 10, 13, 16, 17, 21\n"
            f"  Норма: 0-9 | Лёгкая: 10-13 | Умеренная: 14-20 | Тяжёлая: 21+ | Оч. тяжёлая: 28+\n\n"
            f"**Тревога (A):** {a} баллов — *{al}*\n"
            f"  Вопросы: 2, 4, 7, 9, 15, 19, 20\n"
            f"  Норма: 0-7 | Лёгкая: 8-9 | Умеренная: 10-14 | Тяжёлая: 15+ | Оч. тяжёлая: 20+\n\n"
            f"**Стресс (S):** {s} баллов — *{sl}*\n"
            f"  Вопросы: 1, 6, 8, 11, 12, 14, 18\n"
            f"  Норма: 0-14 | Лёгкая: 15-18 | Умеренная: 19-25 | Тяжёлая: 26+ | Оч. тяжёлая: 34+\n\n"
            f"⚠️ Это скрининг, не диагноз. Результаты выше нормы — повод обратиться к специалисту."
        )
    else:
        level = test_level(score, sess["levels"])
        db.save_test_result(msg.chat.id, sess["tid"], score, level)
        text = (
            f"📋 **{TESTS_MENU[sess['tid']]['name']} завершён!**\n\n"
            f"Твой результат: **{score} баллов** — {level}.\n\n"
            "⚠️ Это не диагноз. Тест показывает текущее состояние."
        )
    await msg.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")


# ===== LUSCHER TEST =====
async def start_luscher(callback: types.CallbackQuery):
    _test_sessions[callback.from_user.id] = {"tid": "luscher", "round": 1, "step": 0, "picked": [], "order1": [], "order2": []}
    await callback.answer()
    await show_luscher_colors(callback.message, callback.from_user.id)


async def show_luscher_colors(msg, uid):
    sess = _test_sessions.get(uid)
    if not sess:
        return
    if sess["step"] >= len(LUSCHER_COLORS):
        if sess["round"] == 1:
            sess["order1"] = sess["picked"][:]
            sess["round"] = 2
            sess["step"] = 0
            sess["picked"] = []
            shuffled = list(range(8))
            random.shuffle(shuffled)
            sess["shuffle"] = shuffled
            text = "🎨 **Тест Люшера — 2-й раунд**\n\nТеперь выбери цвета снова. Не старайся вспомнить предыдущий выбор — доверься первому впечатлению.\n\n"
            remaining = [(i, LUSCHER_COLORS[i][0], LUSCHER_COLORS[i][1]) for i in shuffled]
            buttons = [[InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"lusch_pick_{i}")] for i, emoji, name in remaining]
            await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
        else:
            await finish_luscher(msg, uid)
        return

    step = sess["step"]
    remaining = [(i, LUSCHER_COLORS[i][0], LUSCHER_COLORS[i][1]) for i in (range(8) if sess["round"] == 1 else sess.get("shuffle", range(8))) if i not in sess["picked"]]
    text = f"🎨 **Тест Люшера{' — 2-й раунд' if sess['round'] == 2 else ''}**\n\nВыбери **{step+1}-й** цвет (самый приятный из оставшихся):\n\n"
    if sess["picked"]:
        picked_str = ", ".join(f"{LUSCHER_COLORS[i][0]}({p+1})" for p, i in enumerate(sess["picked"]))
        text += f"Уже выбрано: {picked_str}\n\n"
    buttons = [[InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"lusch_pick_{i}")] for i, emoji, name in remaining]
    await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")


@router.callback_query(F.data.startswith("lusch_pick_"))
async def luscher_pick(callback: types.CallbackQuery):
    uid = callback.from_user.id
    idx = int(callback.data.split("_")[-1])
    sess = _test_sessions.get(uid)
    if not sess:
        await callback.answer("Тест не найден.", show_alert=True)
        return
    sess["picked"].append(idx)
    sess["step"] += 1
    await callback.answer()
    await show_luscher_colors(callback.message, uid)


async def finish_luscher(msg, uid):
    sess = _test_sessions.pop(uid, None)
    if not sess:
        return
    order1 = sess["order1"]
    order2 = sess["picked"]
    pos1 = {c: i for i, c in enumerate(order1)}
    pos2 = {c: i for i, c in enumerate(order2)}

    text = "🎨 **Тест Люшера завершён!**\n\n"
    text += "**1-й раунд:**\n"
    for i, c in enumerate(order1):
        text += f"  {i+1}. {LUSCHER_COLORS[c][0]} {LUSCHER_COLORS[c][1]}\n"
    text += "\n**2-й раунд:**\n"
    for i, c in enumerate(order2):
        text += f"  {i+1}. {LUSCHER_COLORS[c][0]} {LUSCHER_COLORS[c][1]}\n"

    text += "\n**Интерпретация:**\n"
    primary = {0, 1, 2, 3}
    stable = [c for c in range(8) if abs(pos1.get(c, 8) - pos2.get(c, 8)) <= 1]
    unstable = [c for c in range(8) if abs(pos1.get(c, 8) - pos2.get(c, 8)) >= 3]
    prim_first = sum(1 for c in range(4) if pos1.get(c, 8) < 4 and pos2.get(c, 8) < 4)
    prim_last = sum(1 for c in range(4) if pos1.get(c, 8) >= 4 and pos2.get(c, 8) >= 4)

    if prim_first >= 3:
        text += "✅ Основные цвета (красный, жёлтый, зелёный, синий) в начале в обоих раундах — эмоциональное равновесие.\n"
    elif prim_first >= 1:
        text += "⚠️ Часть основных цветов в начале — есть ресурс, но нестабильность.\n"
    else:
        text += "🔴 Основные цвета в конце в обоих раундах — возможен стресс или подавленность.\n"

    if len(stable) >= 5:
        text += "📌 Много стабильных выборов — у тебя есть устойчивые ценности и потребности.\n"
    elif len(stable) >= 3:
        text += "📌 Умеренная стабильность — часть потребностей осознана.\n"
    else:
        text += "📌 Мало стабильных выборов — возможна внутренняя растерянность.\n"

    if len(unstable) >= 3:
        text += "🔀 Значительные колебания между раундами — внутренний конфликт, неопределённость.\n"

    for c in stable:
        if c == 3:
            text += "🔵 Синий стабилен — потребность в покое и гармонии.\n"
        elif c == 0:
            text += "🔴 Красный стабилен — уверенность, активность.\n"
        elif c == 2:
            text += "🟢 Зелёный стабилен — потребность в самоутверждении.\n"
        elif c == 1:
            text += "🟡 Жёлтый стабилен — потребность в радости и развитии.\n"

    for c in unstable:
        if c == 7:
            text += "⬛ Чёрный нестабилен — борьба с отрицанием или страхом.\n"
        elif c == 4:
            text += "🟣 Фиолетовый нестабилен — колебания между чувствительностью и рациональностью.\n"
        elif c == 6:
            text += "⬜ Серый нестабилен — желание отгородиться vs потребность в контакте.\n"

    text += "\n*⚠️ Упрощённая трактовка. Полный тест Люшера проводится специалистом.*"

    stable_cnt = len(stable)
    summary_parts = []
    if prim_first >= 3:
        summary_parts.append("эмоциональное равновесие")
    elif prim_first >= 1:
        summary_parts.append("частичный ресурс, нестабильность")
    else:
        summary_parts.append("возможный стресс")

    if stable_cnt >= 5:
        summary_parts.append("устойчивые ценности")
    elif stable_cnt < 3:
        summary_parts.append("внутренняя растерянность")

    if len(unstable) >= 3:
        summary_parts.append("внутренний конфликт")
    if order1[0] == 2:
        summary_parts.append("потребность в стабильности")
    elif order1[0] == 0:
        summary_parts.append("потребность в действии")
    elif order1[0] == 3:
        summary_parts.append("потребность в покое")
    elif order1[0] == 1:
        summary_parts.append("потребность в радости")

    db.save_test_result(uid, "luscher", stable_cnt, ", ".join(summary_parts))
    await msg.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
