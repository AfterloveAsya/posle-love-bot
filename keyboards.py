from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Сегодняшнее задание", callback_data="task")],
        [InlineKeyboardButton(text="📓 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="📊 Моё состояние", callback_data="my_state")],
        [InlineKeyboardButton(text="📋 Мои разборы", callback_data="my_analysis")],
        [InlineKeyboardButton(text="🔍 Углублённый разбор", callback_data="deep_analysis")],
        [InlineKeyboardButton(text="📋 Тесты", callback_data="tests_menu")],
        [InlineKeyboardButton(text="📚 Библиотека техник", callback_data="library")],
        [InlineKeyboardButton(text="🆘 Кризисная помощь", callback_data="crisis")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ]
)

back_to_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
    ]
)

start_diagnosis_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пройти диагностику", callback_data="start_diagnosis")]
    ]
)

diary_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Написать в дневник", callback_data="diary_write")],
        [InlineKeyboardButton(text="📖 Мои записи", callback_data="diary_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
)

settings_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Время рассылки", callback_data="settings_time")],
        [InlineKeyboardButton(text="💎 Подписка", callback_data="subscribe")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
)

time_settings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🕐 8:00 / 20:00", callback_data="time_8_20")],
        [InlineKeyboardButton(text="🕑 9:00 / 21:00", callback_data="time_9_21")],
        [InlineKeyboardButton(text="🕒 10:00 / 22:00", callback_data="time_10_22")],
        [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings")]
    ]
)


def tests_menu_kb():
    from test_data import TESTS_MENU
    kb = [[InlineKeyboardButton(text="📋 Шкала депрессии Бека (BDI)", callback_data="beck_test")]]
    for k, v in TESTS_MENU.items():
        kb.append([InlineKeyboardButton(text=v["name"], callback_data=f"t_start_{k}")])
    kb.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def schema_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Детские и уязвимые режимы", callback_data="lib_schema_det")],
            [InlineKeyboardButton(text="Дезадаптивные копинг-режимы", callback_data="lib_schema_cop")],
            [InlineKeyboardButton(text="Здоровые режимы", callback_data="lib_schema_health")],
            [InlineKeyboardButton(text="🔙 В библиотеку", callback_data="library")],
        ]
    )
