"""
Telegram бот для персонализированных анекдотов с рекомендательной системой.
"""
import asyncio
import logging
import os
import sys
import traceback

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils import executor

# Настройка для Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Минимальное логирование
logging.basicConfig(level=logging.WARNING)

# Импорт базы и рекомендательной системы
try:
    from database_sqlite import db, get_connection
    from recommendations import recommender

    print("✅ База данных и рекомендательная система загружены")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    db = None
    recommender = None

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен
TOKEN = os.getenv("BOT_TOKEN")

# Инициализация хранилища состояний
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, storage=storage)


class AddJokeStates(StatesGroup):
    """
    Состояния для добавления анекдотов.

    :ivar waiting_for_joke: Состояние ожидания текста анекдота
    :ivar waiting_for_confirmation: Состояние ожидания подтверждения
    """

    waiting_for_joke = State()
    waiting_for_confirmation = State()


class TestPreferencesStates(StatesGroup):
    """
    Состояния для тестирования предпочтений.

    :ivar testing: Состояние тестирования предпочтений
    """

    testing = State()


def get_main_keyboard():
    """
    Создает основную клавиатуру бота.

    :returns: Основная клавиатура с кнопками меню
    :rtype: ReplyKeyboardMarkup
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🎲 Новый анекдот"))
    keyboard.add(KeyboardButton("⭐ Избранное"))
    keyboard.add(KeyboardButton("➕ Добавить анекдот"))
    keyboard.add(KeyboardButton("📊 Мои анекдоты"))
    keyboard.add(KeyboardButton("👤 Мой профиль"))
    return keyboard


def get_joke_keyboard(joke_id, user_id=None, is_favorite=False):
    """
    Создает инлайн-клавиатуру для взаимодействия с анекдотом.

    :param joke_id: ID анекдота
    :type joke_id: int
    :param user_id: ID пользователя для проверки избранного
    :type user_id: int or None
    :param is_favorite: Флаг, находится ли анекдот в избранном
    :type is_favorite: bool
    :returns: Инлайн-клавиатура с кнопками лайка, дизлайка и избранного
    :rtype: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(row_width=3)

    if user_id and db:
        favorites = db.get_user_favorites(user_id)
        is_favorite = any(fav["id"] == joke_id for fav in favorites)

    keyboard.add(
        InlineKeyboardButton("👍", callback_data=f"like_{joke_id}"),
        InlineKeyboardButton("👎", callback_data=f"dislike_{joke_id}"),
        InlineKeyboardButton(
            "⭐" if not is_favorite else "💫", callback_data=f"fav_{joke_id}"
        ),
    )
    return keyboard


@dispatcher.message_handler(commands=["start"])
async def start_command(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start с тестированием предпочтений.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :param state: Состояние конечного автомата
    :type state: FSMContext
    :returns: Приветственное сообщение с инструкциями
    """
    await state.finish()

    if db:
        user = db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        # Проверяем, достаточно ли у пользователя взаимодействий
        interactions = db.get_user_interactions(user["id"])

        if len(interactions) < 3:  # Мало данных для персонализации
            await message.answer(
                f"👋 Привет, {message.from_user.first_name}!\n\n"
                "Я — бот с персонализированными анекдотами! 🎭\n\n"
                "Чтобы я лучше понимал ваши предпочтения, "
                "давайте оценим несколько анекдотов.\n\n"
                "Нажмите 🎲 Новый анекдот, чтобы начать!",
                reply_markup=get_main_keyboard(),
            )
        else:
            await message.answer(
                f"👋 С возвращением, {message.from_user.first_name}!\n\n"
                "Я уже изучил ваши предпочтения и готов рекомендовать анекдоты по душе! 🎭\n\n"
                "Нажмите 🎲 Новый анекдот для персонализированной рекомендации!",
                reply_markup=get_main_keyboard(),
            )
    else:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я — бот с анекдотами! Используйте кнопки:",
            reply_markup=get_main_keyboard(),
        )


@dispatcher.message_handler(commands=["help"])
async def help_command(message: types.Message):
    """
    Обработчик команды /help.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Справка по командам и функциям бота
    """
    help_text = (
        "🤖 **Команды бота:**\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущее действие\n"
        "/profile - Показать ваш профиль предпочтений\n\n"
        "🎭 **Кнопки:**\n"
        "• 🎲 Новый анекдот - получить персонализированный анекдот\n"
        "• ➕ Добавить анекдот - добавить свой анекдот\n"
        "• 📊 Мои анекдоты - посмотреть свои анекдоты\n"
        "• ⭐ Избранное - ваши любимые анекдоты\n"
        "• 👤 Мой профиль - ваши предпочтения по темам\n\n"
        "🎯 **Персонализация:**\n"
        "Бот изучает ваши предпочтения по 5 темам:\n"
        "💻 Программисты, 🎓 Студенты, 💼 Работа, 👨‍👩‍👧‍👦 Семья, 🎭 Разное\n\n"
        "Чем больше анекдотов вы оцените, тем точнее рекомендации!"
    )
    await message.answer(help_text, parse_mode="Markdown")


@dispatcher.message_handler(commands=["profile"])
async def profile_command(message: types.Message):
    """
    Показать профиль предпочтений пользователя.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Профиль пользователя с предпочтениями по темам
    :raises ImportError: Если модули базы данных или рекомендаций не загружены
    """
    if not db or not recommender:
        await message.answer("❌ Система рекомендаций не загружена")
        return

    user = db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Получаем профиль
    profile = recommender.get_user_profile(user["id"])

    if not profile:
        await message.answer(
            "📊 У вас еще нет профиля предпочтений.\n"
            "Оцените несколько анекдотов, чтобы я изучил ваши вкусы!",
            reply_markup=get_main_keyboard(),
        )
        return

    # Формируем сообщение с профилем
    profile_text = "👤 **Ваш профиль предпочтений**\n\n"
    profile_text += f"Всего оценок: {profile['total_interactions']}\n\n"

    profile_text += "📈 **Ваши предпочтения по темам:**\n"

    # Сортируем темы по убыванию оценки
    sorted_themes = sorted(profile["themes"], key=lambda x: x["score"], reverse=True)

    for theme in sorted_themes:
        score = theme["score"]
        interactions = theme["interactions"]

        # Определяем уровень предпочтения
        if score > 0.5:
            level = "❤️ Любимая"
        elif score > 0.1:
            level = "👍 Нравится"
        elif score > -0.1:
            level = "😐 Нейтрально"
        elif score > -0.5:
            level = "👎 Не нравится"
        else:
            level = "❌ Не любимая"

        # Создаем прогресс бар
        bar_length = 10
        filled = int((score + 1) / 2 * bar_length)
        progress_bar = "█" * filled + "░" * (bar_length - filled)

        profile_text += (
            f"\n{theme['emoji']} **{theme['name']}**\n"
            f"{progress_bar} ({score:.2f})\n"
            f"{level} • Оценок: {interactions}\n"
        )

    # Рекомендации
    if profile["favorite_theme"]:
        fav_theme = next(
            t for t in profile["themes"] if t["id"] == profile["favorite_theme"]
        )
        profile_text += (
            f"\n🎯 **Чаще всего рекомендую:** {fav_theme['emoji']} {fav_theme['name']}"
        )

    profile_text += (
        "\n\n✨ Продолжайте оценивать анекдоты для более точных рекомендаций!"
    )

    await message.answer(
        profile_text, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )


@dispatcher.message_handler(commands=["cancel"], state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Отмена текущего действия.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :param state: Состояние конечного автомата
    :type state: FSMContext
    :returns: Сообщение об отмене действия
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных действий для отмены.", reply_markup=get_main_keyboard()
        )
        return

    await state.finish()
    await message.answer("❌ Действие отменено.", reply_markup=get_main_keyboard())


@dispatcher.message_handler(lambda message: message.text == "🎲 Новый анекдот")
async def send_personalized_joke(message: types.Message):
    """
    Отправить персонализированный анекдот.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Персонализированный анекдот или сообщение об ошибке
    :raises ImportError: Если модули базы данных или рекомендаций не загружены
    """
    if not db or not recommender:
        await message.answer("❌ Система рекомендаций не загружена")
        return

    user = db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Получаем рекомендованный анекдот
    joke = recommender.get_recommended_joke(user["id"])

    if joke:
        # Формируем сообщение с информацией о теме
        theme_info = ""
        if "theme_name" in joke and "theme_emoji" in joke:
            theme_info = f"\n\n🔖 Тема: {joke['theme_emoji']} {joke['theme_name']}"

            # Добавляем пояснение для новых пользователей
            interactions = len(db.get_user_interactions(user["id"]))
            if interactions < 5:
                theme_info += "\n✨ Я только учусь понимать ваши предпочтения!"

        await message.answer(
            f"🎭 **Анекдот #{joke['id']}:**{theme_info}\n\n{joke['text']}",
            reply_markup=get_joke_keyboard(joke["id"], user["id"]),
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "😔 Нет доступных анекдотов. Попробуйте позже или добавьте свои!",
            reply_markup=get_main_keyboard(),
        )


@dispatcher.message_handler(lambda message: message.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    """
    Показать профиль пользователя.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Профиль пользователя
    """
    await profile_command(message)


@dispatcher.message_handler(lambda message: message.text == "➕ Добавить анекдот")
async def add_joke_start(message: types.Message):
    """
    Начать добавление анекдота.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Инструкции по добавлению анекдота
    """
    await AddJokeStates.waiting_for_joke.set()
    await message.answer(
        "✍️ **Добавление своего анекдота**\n\n"
        "Пожалуйста, пришлите текст анекдота.\n"
        "После проверки он появится в общей базе!\n\n"
        "🎯 **Темы определяются автоматически:**\n"
        "💻 Программисты, 🎓 Студенты, 💼 Работа, 👨‍👩‍👧‍👦 Семья, 🎭 Разное\n\n"
        "📝 **Требования:**\n"
        "• Минимум 10 символов\n"
        "• Максимум 1000 символов\n"
        "• Без оскорблений и спама\n\n"
        "❌ Для отмены отправьте /cancel",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("❌ Отмена")
        ),
    )


@dispatcher.message_handler(state=AddJokeStates.waiting_for_joke)
async def add_joke_text(message: types.Message, state: FSMContext):
    """
    Принять текст анекдота.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :param state: Состояние конечного автомата
    :type state: FSMContext
    :returns: Подтверждение принятия текста или сообщение об ошибке
    :raises ValueError: Если текст не соответствует требованиям
    """
    cancel_phrases = {"/cancel", "❌ Отмена"}
    if message.text in cancel_phrases:
        await state.finish()
        await message.answer(
            "❌ Добавление анекдота отменено.", reply_markup=get_main_keyboard()
        )
        return

    text = message.text.strip()

    # Проверки
    if len(text) < 10:
        await message.answer("❌ Анекдот слишком короткий. Минимум 10 символов.")
        return

    if len(text) > 1000:
        await message.answer("❌ Анекдот слишком длинный. Максимум 1000 символов.")
        return

    # Проверка на запрещенные слова
    forbidden_words = {
        "реклама",
        "купить",
        "продать",
        "http://",
        "https://",
        ".ru",
        ".com",
    }
    if any(word in text.lower() for word in forbidden_words):
        await message.answer("❌ Текст содержит запрещенные слова.")
        return

    # Определяем темы анекдота
    themes = db.classify_joke(text)
    themes_text = ""

    # Получаем названия тем
    try:
        theme_names = []
        for theme_id in themes:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, emoji FROM themes WHERE id = ?", (theme_id,)
                )
                row = cursor.fetchone()
                if row:
                    theme_names.append(f"{row['emoji']} {row['name']}")

        if theme_names:
            themes_text = "\n\n🎯 **Определены темы:** " + ", ".join(theme_names)
    except Exception as e:  # pylint: disable=broad-except
        print(f"❌ Ошибка получения тем: {e}")
        themes_text = ""

    # Сохраняем текст и темы в состоянии
    await state.update_data(joke_text=text, joke_themes=themes)
    await AddJokeStates.waiting_for_confirmation.set()

    await message.answer(
        f"📝 **Ваш анекдот:**\n\n{text}{themes_text}\n\n"
        "Всё верно? Отправьте 'да' для подтверждения или 'нет' для изменения.",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        .add(KeyboardButton("✅ Да"))
        .add(KeyboardButton("❌ Нет"))
        .add(KeyboardButton("❌ Отмена")),
    )


@dispatcher.message_handler(state=AddJokeStates.waiting_for_confirmation)
async def add_joke_confirmation(message: types.Message, state: FSMContext):
    """
    Подтверждение добавления анекдота.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :param state: Состояние конечного автомата
    :type state: FSMContext
    :returns: Результат добавления анекдота
    :raises ValueError: Если текст анекдота не найден
    """
    cancel_phrases = {"/cancel", "❌ Отмена"}
    if message.text in cancel_phrases:
        await state.finish()
        await message.answer(
            "❌ Добавление анекдота отменено.", reply_markup=get_main_keyboard()
        )
        return

    negative_responses = {"нет", "no", "изменить", "❌ нет"}
    if message.text.lower() in negative_responses:
        await AddJokeStates.waiting_for_joke.set()
        await message.answer(
            "🔄 Хорошо, пришлите исправленный текст анекдота:",
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
                KeyboardButton("❌ Отмена")
            ),
        )
        return

    positive_responses = {"да", "yes", "✅ да"}
    if message.text.lower() in positive_responses:
        # Получаем сохраненный текст
        data = await state.get_data()
        joke_text = data.get("joke_text", "")

        if not joke_text:
            await state.finish()
            await message.answer(
                "❌ Ошибка: текст анекдота не найден.", reply_markup=get_main_keyboard()
            )
            return

        # Добавляем анекдот в базу
        user = db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        result = db.add_user_joke(joke_text, user["id"])

        if result:
            pending_count = db.get_pending_jokes_count()
            # Упрощенное сообщение без тем
            await message.answer(
                f"✅ **Ваш анекдот добавлен на модерацию!**\n\n"
                f"📊 Номер в очереди: #{result['joke_id']}\n"
                f"⏳ Всего на модерации: {pending_count} анекдотов\n\n"
                f"После проверки ваш анекдот появится в общей базе.\n"
                f"Используйте '📊 Мои анекдоты' чтобы отслеживать статус.\n\n"
                f"Спасибо за вклад! 🎉",
                reply_markup=get_main_keyboard(),
            )
        else:
            await message.answer(
                "❌ Не удалось добавить анекдот. Попробуйте позже.",
                reply_markup=get_main_keyboard(),
            )

        await state.finish()
        return

    # Если ответ не распознан
    await message.answer(
        "Пожалуйста, отправьте 'да' для подтверждения или 'нет' для изменения."
    )


@dispatcher.message_handler(lambda message: message.text == "📊 Мои анекдоты")
async def show_my_jokes(message: types.Message):
    """
    Показать анекдоты пользователя.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Список анекдотов пользователя с их статусами
    :raises ImportError: Если база данных не загружена
    """
    if not db:
        await message.answer("❌ База данных не загружена")
        return

    user = db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    jokes = db.get_user_jokes(user["id"])

    if not jokes:
        await message.answer(
            "📭 У вас пока нет добавленных анекдотов.\n"
            "Используйте '➕ Добавить анекдот' чтобы добавить первый!",
            reply_markup=get_main_keyboard(),
        )
        return

    # Группируем по статусу
    pending = [j for j in jokes if j["status"] == "pending"]
    approved = [j for j in jokes if j["status"] == "approved"]
    rejected = [j for j in jokes if j["status"] == "rejected"]

    text = (
        f"📚 **Мои анекдоты**\n\n"
        f"Всего: {len(jokes)}\n"
        f"⏳ На модерации: {len(pending)}\n"
        f"✅ Одобрено: {len(approved)}\n"
        f"❌ Отклонено: {len(rejected)}\n\n"
    )

    if pending:
        text += "⏳ **На проверке:**\n"
        for joke in pending[:3]:
            short_text = (
                joke["text"][:50] + "..." if len(joke["text"]) > 50 else joke["text"]
            )
            text += f"🔹 #{joke['id']}: {short_text}\n"
        if len(pending) > 3:
            text += f"... и еще {len(pending) - 3}\n"

    if approved:
        text += "\n✅ **Одобренные:**\n"
        for joke in approved[:2]:
            short_text = (
                joke["text"][:50] + "..." if len(joke["text"]) > 50 else joke["text"]
            )
            text += f"#{joke['id']}: {short_text}\n"

    if rejected:
        text += "\n❌ **Отклоненные:**\n"
        for joke in rejected[:2]:
            short_text = (
                joke["text"][:50] + "..." if len(joke["text"]) > 50 else joke["text"]
            )
            text += f"#{joke['id']}: {short_text}\n"

    text += "\n✍️ Хотите добавить еще? Используйте '➕ Добавить анекдот'"

    await message.answer(text, reply_markup=get_main_keyboard())


@dispatcher.message_handler(lambda message: message.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    """
    Показать избранные анекдоты пользователя.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Список избранных анекдотов пользователя
    :raises ImportError: Если база данных не загружена
    """
    if not db:
        await message.answer("❌ База данных не загружена")
        return

    user = db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    favorites = db.get_user_favorites(user["id"])

    if not favorites:
        await message.answer(
            "📭 У вас пока нет избранных анекдотов.\n"
            "Читайте анекдоты и нажимайте ⭐ чтобы добавлять!",
            reply_markup=get_main_keyboard(),
        )
        return

    # Отправляем первый анекдот с возможностью листать
    await message.answer(
        f"⭐ **Ваши избранные анекдоты ({len(favorites)}):**\n\n"
        f"1. {favorites[0]['text']}",
        reply_markup=get_joke_keyboard(favorites[0]["id"], user["id"]),
    )

    # Отправляем остальные (если есть)
    for i, joke in enumerate(favorites[1:], 2):
        await asyncio.sleep(0.1)  # Небольшая задержка
        await message.answer(
            f"{i}. {joke['text']}",
            reply_markup=get_joke_keyboard(joke["id"], user["id"]),
        )


@dispatcher.callback_query_handler(
    lambda c: c.data.startswith("like_") or c.data.startswith("dislike_")
)
async def process_like_dislike(callback_query: types.CallbackQuery):
    """
    Обработка лайков и дизлайков.

    :param callback_query: Объект callback запроса
    :type callback_query: types.CallbackQuery
    :returns: Результат оценки анекдота
    :raises ValueError: Если не удалось распарсить данные callback
    :raises KeyError: Если отсутствуют необходимые данные
    """
    try:
        await callback_query.answer()
        action, joke_id = callback_query.data.split("_")
        joke_id = int(joke_id)
        liked = action == "like"

        if db:
            user = db.get_or_create_user(
                telegram_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name,
            )

            # Добавляем взаимодействие
            db.add_interaction(user["id"], joke_id, liked)

            # Обновляем предпочтения пользователя
            db.update_user_preference(user["id"], joke_id, liked)

            if liked:
                await callback_query.message.answer(
                    "✅ Отлично! Теперь я знаю, что вам нравятся такие анекдоты!"
                )
            else:
                await callback_query.message.answer(
                    "📝 Понял! Буду реже предлагать такие анекдоты."
                )

    except (ValueError, KeyError, AttributeError) as e:
        print(f"❌ Ошибка обработки оценки: {e}")


@dispatcher.callback_query_handler(lambda c: c.data.startswith("fav_"))
async def process_favorite(callback_query: types.CallbackQuery):
    """
    Обработка добавления в избранное.

    :param callback_query: Объект callback запроса
    :type callback_query: types.CallbackQuery
    :returns: Результат добавления/удаления из избранного
    :raises ValueError: Если не удалось распарсить данные callback
    :raises AttributeError: Если отсутствуют необходимые данные
    """
    try:
        _, joke_id = callback_query.data.split("_")
        joke_id = int(joke_id)

        if db:
            user = db.get_or_create_user(
                telegram_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name,
            )
            success, message_text = db.add_favorite(user["id"], joke_id)
            await callback_query.answer(message_text, show_alert=False)

            # Обновляем кнопку в сообщении
            if success:
                await callback_query.message.edit_reply_markup(
                    get_joke_keyboard(joke_id, user["id"], True)
                )
            else:
                await callback_query.message.edit_reply_markup(
                    get_joke_keyboard(joke_id, user["id"], False)
                )

    except (ValueError, KeyError, AttributeError) as e:
        print(f"❌ Ошибка избранного: {e}")
        await callback_query.answer("❌ Ошибка", show_alert=False)


@dispatcher.message_handler(state="*")
async def text_handler(message: types.Message):
    """
    Обработка остальных текстовых сообщений.

    :param message: Объект сообщения от пользователя
    :type message: types.Message
    :returns: Ответ на общие фразы или предложение использовать меню
    """
    text = message.text.lower()

    # Если пользователь в состоянии, пропускаем
    current_state = dispatcher.current_state(
        chat=message.chat.id, user=message.from_user.id
    )
    state = await current_state.get_state()
    if state:
        return

    # Обработка общих фраз
    if any(word in text for word in ["привет", "здравствуй", "hi", "hello"]):
        await message.answer(f"👋 Привет, {message.from_user.first_name}!")
    elif any(word in text for word in ["спасибо", "thanks", "thank"]):
        await message.answer("🙏 Пожалуйста! Рад помочь!")
    elif any(word in text for word in ["пока", "до свидания", "bye"]):
        await message.answer("👋 До новых встреч!")
    elif "анекдот" in text:
        await send_personalized_joke(message)
    else:
        await message.answer(
            "🤔 Не понял запрос. Используйте кнопки меню:",
            reply_markup=get_main_keyboard(),
        )


async def on_startup(_):
    """
    Действия при запуске бота.

    :param _: Неиспользуемый параметр (обычно dispatcher)
    :returns: Информация о запуске бота в консоль
    """
    print("=" * 60)
    print("🤖 БОТ С ПЕРСОНАЛИЗИРОВАННЫМИ АНЕКДОТАМИ")
    print("=" * 60)

    if db:
        pending_count = db.get_pending_jokes_count()
        print("✅ База данных готова")
        print(f"⏳ Анекдотов на модерации: {pending_count}")

        # Проверяем количество анекдотов по темам
        try:
            stats = db.get_themes_statistics()

            if stats:
                print("\n📊 Анекдоты по темам:")
                for stat in stats:
                    name = stat.get("name", "Неизвестно")
                    count = stat.get("count", 0)
                    approved = stat.get("approved", 0)
                    total = stat.get("total", count)

                    if "approved" in stat and "total" in stat:
                        print(f"  {name}: {approved}/{total} (одобрено/всего)")
                    else:
                        print(f"  {name}: {count}")
            else:
                print("\n📊 Нет данных по темам")

        except (ValueError, KeyError, AttributeError) as e:
            print(f"⚠️ Не удалось получить статистику тем: {e}")
            traceback.print_exc()

    print("\n🎯 **Доступные функции:**")
    print("🎲 Новый анекдот - персонализированные рекомендации")
    print("➕ Добавить анекдот - добавить свой анекдот")
    print("📊 Мои анекдоты - отслеживать статус своих анекдотов")
    print("⭐ Избранное - ваши любимые анекдоты")
    print("👤 Мой профиль - ваши предпочтения по темам")
    print("=" * 60)


if __name__ == "__main__":
    executor.start_polling(dispatcher, skip_updates=True, on_startup=on_startup)
