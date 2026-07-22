import random
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import db
from tasks_data import TASKS
from keyboards import main_menu_kb, back_to_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu_kb)


@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb)
    await callback.answer()


@router.callback_query(F.data == "my_state")
async def show_my_state(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text("Ты ещё не проходил(а) диагностику.", reply_markup=kb)
    else:
        emoji = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢", "здоров": "⭐"}
        user_state = user_data.get("state")
        if not user_state:
            tb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text("Ты ещё не проходил(а) диагностику.", reply_markup=tb)
            await callback.answer()
            return
        total = user_data["score"] or 0
        updated = user_data.get("updated_at", "")[:10] if user_data.get("updated_at") else "—"
        level = "🔴 Кризис" if total >= 15 else ("🟡 Стабилизация" if total >= 7 else ("🟢 Восстановление" if total >= 3 else "⭐ Здоров"))
        progress_bar = "🟥" * min(total, 21) + "⬜" * (21 - min(total, 21))
        premium = "⭐ Premium" if db.is_premium(callback.from_user.id) else "—"
        diary_n = db.get_diary_count(callback.from_user.id)
        analysis_n = db.get_analysis_count(callback.from_user.id)
        streak = db.get_streak_count(callback.from_user.id)
        diag_log = db.get_diagnosis_log(callback.from_user.id, limit=5)

        text = (
            f"{emoji.get(user_state, '')} **Твоё состояние:** {level}\n\n"
            f"`{progress_bar}`\nБаллов: {total}/21\n"
            f"Последняя диагностика: {updated}\n"
            f"Статус: {premium}\n"
            f"📔 Записей в дневнике: {diary_n}"
        )
        if streak > 1:
            text += f"\n🔥 Дней подряд: {streak}"
        text += f"\n📋 Разборов: {analysis_n}\n"
        test_results = db.get_test_results(callback.from_user.id, limit=5)
        if test_results:
            text += "\n**Последние тесты:**\n"
            names = {"bdi": "BDI", "bai": "BAI", "bhs": "BHS", "gad7": "GAD-7", "ptgi": "PTGI", "dass21": "DASS-21", "luscher": "Люшер"}
            for t in test_results:
                label = names.get(t["test_id"], t["test_id"])
                text += f"  {t['timestamp'][:10]}: {label} — {t['score']} баллов\n"
        if len(diag_log) > 1:
            text += "\n**История диагностик:**\n"
            for d in diag_log:
                e = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢", "здоров": "⭐"}.get(d['state'], '')
                text += f"  {d['timestamp'][:10]}: {e} {d['score']} баллов\n"
        text += "\nМожешь пройти диагностику заново в любой момент."
        buttons = [[InlineKeyboardButton(text="🔄 Пройти заново", callback_data="start_diagnosis")],
                   [InlineKeyboardButton(text="📋 Полная карта", callback_data="diag_card")]]
        if test_results:
            for t in reversed(test_results[-3:]):
                label = names.get(t["test_id"], t["test_id"])
                buttons.append([InlineKeyboardButton(text=f"📊 {t['timestamp'][:10]} {label} ({t['score']})", callback_data=f"tview_{t['id']}")])
        buttons.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "diag_card")
async def diagnostic_card(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user_data = db.get_user_state(uid)
    if not user_data or not user_data.get("state"):
        await callback.message.edit_text("Сначала пройди диагностику через /start.", reply_markup=back_to_menu_kb)
        await callback.answer()
        return
    total = user_data["score"] or 0
    emoji = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢", "здоров": "⭐"}
    level = "🔴 Кризис" if total >= 15 else ("🟡 Стабилизация" if total >= 7 else ("🟢 Восстановление" if total >= 3 else "⭐ Здоров"))
    bar = "🟥" * min(total, 21) + "⬜" * (21 - min(total, 21))
    premium = "⭐ Premium" if db.is_premium(uid) else "—"

    lines = [f"📋 **Диагностическая карта**\n"]
    lines.append(f"{emoji.get(user_data.get('state',''),'')} **{level}**")
    lines.append(f"`{bar}`  {total}/21 баллов")
    lines.append(f"Статус: {premium}\n")

    diag_log = db.get_diagnosis_log(uid, limit=10)
    if diag_log:
        lines.append("**📈 История диагностик:**")
        for d in diag_log:
            e = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢", "здоров": "⭐"}.get(d['state'], '')
            lines.append(f"{d['timestamp'][:10]}: {e} {d['state']} ({d['score']})")

    tests = db.get_test_results(uid, limit=10)
    if tests:
        lines.append("\n**📊 Результаты тестов:**")
        names = {"bdi": "BDI", "bai": "BAI", "bhs": "BHS", "gad7": "GAD-7", "ptgi": "PTGI", "dass21": "DASS-21", "luscher": "Люшер"}
        for t in tests:
            label = names.get(t["test_id"], t["test_id"])
            lines.append(f"{t['timestamp'][:10]}: {label} — {t['score']} баллов")

    analyses = db.get_all_analyses(uid, limit=5)
    if analyses:
        lines.append("\n**📋 Разборы:**")
        for a in analyses:
            e = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢", "здоров": "⭐"}.get(a['state'], '')
            lines.append(f"{a['timestamp'][:10]}: {e} {a['state']} ({a['score']})")

    lines.append(f"\n📔 Записей в дневнике: {db.get_diary_count(uid)}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
        ]), parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "my_analysis")
async def show_my_analysis(callback: types.CallbackQuery):
    analyses = db.get_all_analyses(callback.from_user.id, limit=20)
    if not analyses:
        await callback.message.edit_text(
            "У тебя пока нет сохранённых разборов. Пройди диагностику и ответь на вопросы, чтобы получить экспертный анализ.",
            reply_markup=back_to_menu_kb
        )
        await callback.answer()
        return
    text = "📋 **Мои разборы**\n\nНажми на разбор, чтобы открыть:\n"
    buttons = []
    for a in analyses:
        date = a["timestamp"][:10]
        em = {"кризис": "🔴", "стабилизация": "🟡", "восстановление": "🟢", "здоров": "⭐"}.get(a["state"], "")
        buttons.append([InlineKeyboardButton(text=f"{em} {date} — {a['score']} баллов", callback_data=f"aview_{a['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("aview_"))
async def analysis_view(callback: types.CallbackQuery):
    aid = int(callback.data.split("_")[-1])
    a = db.get_analysis_by_id(aid, callback.from_user.id)
    if not a:
        await callback.answer("Разбор не найден.", show_alert=True)
        return
    state_name = a["state"].capitalize()
    text = (
        f"📋 **Разбор от {a['timestamp'][:10]}**\n"
        f"Состояние: **{state_name}** ({a['score']} баллов)\n\n"
        f"{a['analysis']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку разборов", callback_data="my_analysis")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("tview_"))
async def test_view(callback: types.CallbackQuery):
    tid = int(callback.data.split("_")[-1])
    t = db.get_test_result_by_id(tid, callback.from_user.id)
    if not t:
        await callback.answer("Результат не найден.", show_alert=True)
        return
    names = {"bdi": "BDI (депрессия)", "bai": "BAI (тревога)", "bhs": "BHS (безнадёжность)", "gad7": "GAD-7 (тревога)", "ptgi": "PTGI (посттравматический рост)", "dass21": "DASS-21 (депрессия/тревога/стресс)", "luscher": "Тест Люшера"}
    label = names.get(t["test_id"], t["test_id"])
    text = (
        f"📊 **{label}**\n"
        f"Дата: {t['timestamp'][:10]}\n"
        f"Результат: **{t['score']} баллов**\n"
    )
    if t["details"]:
        text += f"Интерпретация: {t['details']}\n"
    if t["test_id"] == "dass21" and t["details"]:
        for part in t["details"].split(", "):
            text += f"  • {part}\n"
    text += "\n⚠️ Это не диагноз. Тест показывает текущее состояние."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К состоянию", callback_data="my_state")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "task")
async def show_task(callback: types.CallbackQuery):
    user_data = db.get_user_state(callback.from_user.id)
    if user_data is None:
        text = "Сначала пройди диагностику. Нажми /start."
    else:
        state = user_data["state"]
        pool = list(TASKS.get(state, TASKS["стабилизация"]))
        tests = db.get_test_results(callback.from_user.id, limit=5)
        if tests:
            for t in tests:
                if t["test_id"] == "bai" and t["score"] >= 10:
                    pool.append("🌊 **Заземление:** Умойся холодной водой и сделай квадратное дыхание (4-4-4-4).")
                    pool.append("🧊 **Лёд:** Подержи кубик льда в руке 30 секунд, концентрируясь на ощущении.")
                if t["test_id"] == "bdi" and t["score"] >= 14:
                    pool.append("🌱 **Маленький шаг:** Сделай сегодня одно простое действие — заправь постель или выйди на 5 мин.")
                    pool.append("☀️ **Свет:** Посиди на солнце или у окна 10 минут, закрыв глаза.")
                if t["test_id"] == "gad7" and t["score"] >= 10:
                    pool.append("📝 **Выгрузи тревогу:** Напиши список «что меня тревожит» и раздели на контролируемое/неконтролируемое.")
                if t["test_id"] == "ptgi" and t["score"] < 21:
                    pool.append("💎 **Одна хорошая вещь:** Вспомни и запиши 1 качество, которое ты открыл(а) в себе после расставания.")
                if t["test_id"] == "bhs" and t["score"] >= 9:
                    pool.append("🌟 **Якорь будущего:** Представь себя через год — где ты, кто рядом, что чувствуешь. Запиши 3 детали.")
        chosen = random.choice(pool)
        text = f"📋 **Твоё задание на сегодня:**\n\n{chosen}\n\nВозвращайся завтра за новым!"
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "crisis")
async def crisis_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🆘 **Экстренная помощь**\n\n"
        "Сделай прямо сейчас:\n"
        "1. Умойся холодной водой или подержи руки под холодной водой.\n"
        "2. Сделай 5 глубоких вдохов (вдох на 4 счёта, выдох на 6).\n"
        "3. Повторяй: «Я в безопасности. Это чувство пройдёт».\n\n"
        "📞 **Телефоны доверия (Россия):**\n"
        "• 8 (800) 333-44-34\n"
        "• 8 (800) 2000-122 (для детей и подростков)\n"
        "• 112 — экстренная служба",
        reply_markup=back_to_menu_kb, parse_mode="Markdown"
    )
    await callback.answer()
