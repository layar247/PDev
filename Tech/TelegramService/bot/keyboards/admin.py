from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить тему")],
            [KeyboardButton(text="Импорт тем из Excel")],
            [KeyboardButton(text="Список тем")],
            [KeyboardButton(text="Добавить администратора")],
            [KeyboardButton(text="Удалить администратора")],
            [KeyboardButton(text="Список администраторов")],
            [KeyboardButton(text="В главное меню")]
        ],
        resize_keyboard=True
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )

