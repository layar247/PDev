from aiogram import Router, F
from aiogram.types import Message, CallbackQuery,InlineKeyboardMarkup,InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
router = Router()
from database.models import User,Topic,SurveyAnswer
from database.utils import async_session
from keyboards.user import main_menu_kb,survey_active_kb, survey_start_kb, get_question_kb,departments_kb
from texts import START_TEXT, SURVEY_START_TEXT, LINKS
from survey_data import SURVEY_QUESTIONS, TOPICS
from sqlalchemy import select
class SurveyStates(StatesGroup):
    answering = State()
    completed = State()

@router.message(Command("start"))
async def start(message: Message):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=message.from_user.id,
                full_name=message.from_user.full_name,
                username=message.from_user.username
            )
            session.add(user)
            await session.commit()

    # Получаем username или альтернативу
    username = message.from_user.username
    if username:
        username_str = f"@{username}"
    else:
        username_str = message.from_user.full_name  # или first_name

    # Подставляем в шаблон из texts.py
    caption = START_TEXT.format(username=username_str)

    photo = 'AgACAgIAAxkBAAIMEWnvozDHP41JeZ2iApv9tQyEQTgPAALmEmsbveCAS3Nm5Pvd_1sEAQADAgADeAADOwQ'
    await message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )

@router.message(F.text == "Пройти опрос")
async def start_survey(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == SurveyStates.answering:
        await message.answer("⚠️ Опрос уже идёт! Завершите его или "
                             "используйте кнопку «Пройти опрос заново».")
        return
    await message.answer(SURVEY_START_TEXT, reply_markup=survey_start_kb())

@router.callback_query(F.data == "start_survey")
async def start_survey_callback(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == SurveyStates.answering:
        await callback.answer("⚠️Опрос уже идёт!\nВы можете перезапустить "
                              "опрос или отменить "
                              "его соответсвующими кнопками в правом "
                              "нижнем углу экрана.", show_alert=True)
        return

    await state.set_data({
        'current_question': 0,
        'answers': [],
        'user_weights': [0] * 8
    })
    await state.set_state(SurveyStates.answering)

    # замена Пройти опрос на Пройти опрос заново
    await callback.message.answer(
        "Опрос начат. Для перезапуска используйте кнопку «Пройти опрос заново».",
        reply_markup=survey_active_kb()
    )
    await show_question(callback.message, state)
    await callback.answer()
@router.message(F.text == "Пройти опрос заново")
async def restart_survey(message: Message, state: FSMContext):

    await state.clear()

    await state.set_data({
        'current_question': 0,
        'answers': [],
        'user_weights': [0] * 8
    })
    await state.set_state(SurveyStates.answering)

    await message.answer(
        "Опрос перезапущен. Для отмены используйте «Отменить опрос».",
        reply_markup=survey_active_kb()
    )
    await show_question(message, state)

async def show_question(message: Message, state: FSMContext):
    data = await state.get_data()
    question = SURVEY_QUESTIONS[data['current_question']]
    buttons = [
        [InlineKeyboardButton(text=option, callback_data=f"answer_{question['id']}_{idx}")]
        for idx, option in enumerate(question['options'])
    ]

    await message.answer(
        f"Вопрос {data['current_question'] + 1}/{len(SURVEY_QUESTIONS)}:\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(SurveyStates.answering)
@router.callback_query(F.data == "cancel_active_survey", SurveyStates.answering)
async def cancel_active_survey(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Опрос отменён.", reply_markup=main_menu_kb())
    await callback.answer()
async def set_active_survey_keyboard(message: Message):
    await message.answer(
        "Опрос начат. Для перезапуска используйте кнопку «Пройти опрос заново».",
        reply_markup=survey_active_kb()
    )

@router.callback_query(F.data.startswith("answer_"), SurveyStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if 'current_question' not in data:
        await callback.message.answer("Сессия опроса утеряна. Пожалуйста, начните опрос заново.")
        await state.clear()
        return
    question_idx = data['current_question']
    question = SURVEY_QUESTIONS[question_idx]

    # Разбираем callback_data: ожидаем "answer_<question_id>_<answer_idx>"
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("Некорректный формат ответа", show_alert=True)
        return

    try:
        qid = int(parts[1])
        answer_idx = int(parts[2])
    except ValueError:
        await callback.answer("Ошибка обработки ответа", show_alert=True)
        return

    # Проверяем, что вопрос в callback_data совпадает с текущим
    if qid != question['id']:
        await callback.answer("Этот вопрос уже неактуален", show_alert=True)
        return

    try:
        if answer_idx >= len(question['weights']):
            raise IndexError("Invalid answer index")

        new_weights = [
            data['user_weights'][i] + question['weights'][answer_idx][i]
            for i in range(len(data['user_weights']))
        ]
        new_answers = data['answers'] + [{
            'question_id': question['id'],
            'answer_idx': answer_idx
        }]

        if question_idx + 1 < len(SURVEY_QUESTIONS):
            await state.update_data({
                'current_question': question_idx + 1,
                'answers': new_answers,
                'user_weights': new_weights
            })
            await show_question(callback.message, state)
        else:
            await state.update_data({
                'answers': new_answers,
                'user_weights': new_weights
            })
            await recommend_topics(callback.message, state)
            await state.clear()

    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка обработки ответа: {str(e)}")
        await state.clear()

    await callback.answer()

async def recommend_topics(message: Message, state: FSMContext):
    data = await state.get_data()
    user_weights = data['user_weights']

    # Нормализация
    total = sum(user_weights) or 1
    normalized = [w / total for w in user_weights]

    # Загружаем все темы из БД
    async with async_session() as session:
        result = await session.execute(select(Topic))
        topics = result.scalars().all()

    valid_topics = [
        t for t in topics
        if t.weights and any(w != 0 for w in t.weights)
    ]

    if not valid_topics:
        await message.answer("❌ Пока нет подходящих тем.")
        await state.clear()
        return

    scored = []
    for topic in valid_topics:
        score = sum(
            float(normalized[i]) * float(topic.weights[i])
            for i in range(min(len(normalized), len(topic.weights)))
        )
        scored.append((topic, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    max_score = scored[0][1] if scored else 0

    response = "🏆 Рекомендованные темы:\n\n"
    for topic, score in scored[:5]:
        percent = int(round(score / max_score * 100)) if max_score != 0 else 0
        response += (
            f"🔹 <b>{topic.title}</b>\n"
            f"📊 Сложность: {topic.difficulty.capitalize()}\n"
            f"📝 Описание: {topic.description}\n"
            f"🎯 Направление: {topic.direction.upper()}\n"
            f"📈 Соответствие: {percent}%\n\n"
        )

    response += "ℹ️ Также рекомендую ознакомиться с другими полезными функциями бота в меню."
    await message.answer(response, parse_mode="HTML", reply_markup=main_menu_kb())
    await state.clear()
@router.callback_query(F.data == "cancel_survey")
async def cancel_survey(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == SurveyStates.answering:
        await callback.answer(
            "❌Кнопка не актуальна."
            "Воспользуйтесь действующими командами "
            "из панели в нижнем правом углу экрана.",
            show_alert=True
        )
        return
    await callback.answer("Нет активного опроса.", show_alert=True)
@router.message(F.text == "Отменить опрос")
async def cancel_survey_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Опрос отменён.", reply_markup=main_menu_kb())
@router.message(Command("survey"))
async def survey_command(message: Message, state: FSMContext):
    await start_survey(message, state)

@router.message(Command("faculty"))
async def faculty_command(message: Message):
    await faculty_link(message)

@router.message(Command("vk"))
async def vk_command(message: Message):
    await vk_link(message)

@router.message(Command("materials"))
async def materials_command(message: Message):
    await materials_link(message)
@router.message(F.text == "Факультет")
async def faculty_link(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт факультета", url=LINKS['faculty'])]
        ]
    )
    await message.answer_photo(
        photo='AgACAgIAAxkBAAIH-mnqDRf-jE3tXbFyahR7JjU-GUkLAAIrFWsbAdFQS44_SNnaYZq4AQADAgADeQADOwQ',
        caption="🎓Здесь вы можете более подробно изучить учебный план сдачи и актуальное расписание\n\n"
                "Также по команде /departments можете более "
                "подробно узнать о всех кафедрах и их научных направлениях.",
        reply_markup=keyboard
    )


@router.message(F.text == "VK группа")
async def vk_link(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на страницу деканата", url=LINKS['vk'])]
        ]
    )
    await message.answer_photo(
        photo='AgACAgIAAxkBAAIII2nqGASRvvp6-e9pTUkQ1xVoItPpAAJqFWsbAdFQS-QGX52a8BvOAQADAgADeQADOwQ',
        caption="Деканат ФКТиПМ на страничке "
                "ВКонтакте всегда публикует и оповещает студентов о каких либо изменниях и сроках сдачи",
        reply_markup=keyboard
    )

@router.message(F.text == "Материалы")
async def materials_link(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт КубГУ", url=LINKS['materials'])]
        ]
    )
    await message.answer_photo(
        photo='AgACAgIAAxkBAAIL9WnvlyrBtp7RYw7hqw1NU8_6kRwRAAKHEmsbveCAS_A9DwbYu_tSAQADAgADeAADOwQ',
        caption="На сайте университета для нашего факультета опубликована страница "
                "с актуальными данными оформления курсовых работ с прилагающимися изменениями",
        reply_markup=keyboard
    )
@router.message(Command("departments"))
async def departments_command(message: Message):
    photo = "AgACAgIAAxkBAAIIOWnqHwGavoBp5o3FdgFb0aJWgW5GAAKDFWsbAdFQSzwxiER8KGalAQADAgADeQADOwQ"
    caption = ("На факультете есть 5 основных кафедр с каждой из которой"
               " ты можешь подробнее ознакомится, нажав на ее аббревиатуру")
    await message.answer_photo(photo=photo, caption=caption, reply_markup=departments_kb())

@router.callback_query(F.data == "dept_kit")
async def dept_kit(callback: CallbackQuery):
    photo = "AgACAgIAAxkBAAIIP2nqIiOfmxmQvC2S9QI45O7zNTyyAAKhFWsbAdFQSylWxzXKhcI4AQADAgADeQADOwQ"
    caption = (
        "<b>Кафедра информационных технологий (КИТ)</b>\n"
        "🌐Научные интересы:Разработка и построение нейросетевых моделей, CRM-системы и автоматизация бизнес-процессов, "
        "современные языки программирования, архитектура ПО, "
        "базы данных, компьютерная безопасность и программная инженерия,мобильные приложения,Data mining,математическое моделирование,"
        "веб-разработка."
    )
    await callback.message.answer_photo(photo=photo, caption=caption,parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "dept_kvt")
async def dept_kvt(callback: CallbackQuery):
    photo = "AgACAgIAAxkBAAIIRmnqJn0EC1ro0L2dIcS_umFYj9eJAAK_FWsbAdFQS7hkitbin68jAQADAgADeAADOwQ"
    caption = (
        "<b>Кафедра вычислительной техники (КВТ)</b>\n"
        "🌐Научные интересы:специализация на аппаратном и программном обеспечении компьютерных "
        "систем, встроенных системах, сетевых "
        "технологиях и параллельных вычислениях,машинное зрение,вычислительные машины и "
        "низкоуровневое программирование, "
        "архитектура ЭВМ, "
        "микроконтроллеры, "
        "операционные системы реального времени,технологии машинного обучения и анализа больших данных."
    )
    await callback.message.answer_photo(photo=photo, caption=caption,parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "dept_kmm")
async def dept_kmm(callback: CallbackQuery):
    photo = "AgACAgIAAxkBAAIISGnqJznLHzPeJKNw5Sh72umJT5KFAALJFWsbAdFQS23Gjtu-q0lfAQADAgADeQADOwQ"
    caption = (
        "<b>Кафедра математического моделирования (КММ)</b>\n"
        "🌐Научные интересы:разработка и исследование математических "
        "моделей в естествознании, экономике и технике,электромембранные системы и"
        "анализ  краевых задач,математические модели экологических процессов,"
        "базы данных и знаний,информационные системы в образовании."

    )
    await callback.message.answer_photo(photo=photo, caption=caption,parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "dept_kadii")
async def dept_kadii(callback: CallbackQuery):
    photo = "AgACAgIAAxkBAAIISmnqKOR84I0OGyBI5d1VRx9bk-P6AALYFWsbAdFQS69EDDzBzLvKAQADAgADeQADOwQ"
    caption = (
        "<b>Кафедра анализа данных и искусственного интеллекта (КАДИИ)</b>\n"
        "🌐Научные интересы:Data Science, машинное обучение,криптография,"
        "Big data и интеллектуальные системы,методы сбора,обработки и анализа информации, "
        "создание моделей прогнозирования, "
        "рекомендательные системы, нейросетевые решения для бизнеса "
        "и науки,интеллектуальные и искусственные нейронные модели,облачные технологии,автоматизация хозяйственной деятельности(1С)."
    )
    await callback.message.answer_photo(photo=photo, caption=caption,parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "dept_kpm")
async def dept_kpm(callback: CallbackQuery):
    photo = "AgACAgIAAxkBAAIITGnqKwWrvluCymw4XlU8mwS9Sok9AAMWaxsB0VBL5Vp27jbQj4oBAAMCAAN5AAM7BA"
    caption = (
        "<b>Кафедра прикладной математики (КПМ)</b>\n"
        "🌐Научные интересы:исследования в области численного и асимптотического "
        "анализа краевых задач для систем уравнений в частных производных и некорректных задач,"
        "математические методы в исследованиях операций, "
        "оптимизаций, математической физике и обработке сигналов,"
        "дискретная математика и комбинаторика, динамические задачи механики."
    )
    await callback.message.answer_photo(photo=photo, caption=caption,parse_mode="HTML")
    await callback.answer()