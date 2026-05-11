from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пройти опрос")]
        ],
        resize_keyboard=True
    )
def survey_active_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пройти опрос заново")],
            [KeyboardButton(text="Отменить опрос")]
        ],
        resize_keyboard=True
    )

def departments_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="КИТ", callback_data="dept_kit"),
                InlineKeyboardButton(text="КВТ", callback_data="dept_kvt"),
                InlineKeyboardButton(text="КММ", callback_data="dept_kmm"),
                InlineKeyboardButton(text="КАДИИ", callback_data="dept_kadii"),
                InlineKeyboardButton(text="КПМ", callback_data="dept_kpm"),
            ]
        ]
    )

def survey_start_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать опрос", callback_data="start_survey")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_survey")]
        ]
    )


def get_question_kb(question_data=None):

    if isinstance(question_data, list):
        options = question_data
    elif isinstance(question_data, dict):
        options = question_data.get('options', [])
    else:
        options = []

    if not options:
        buttons = [[InlineKeyboardButton(text="Продолжить", callback_data="next_question")]]
    else:
        buttons = [
            [InlineKeyboardButton(text=option, callback_data=f"answer_{idx}")]
            for idx, option in enumerate(options)
        ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)