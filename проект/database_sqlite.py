"""
Модуль для работы с базой данных SQLite.
"""
import sqlite3
from contextlib import contextmanager
import os

# Загрузка переменных из .env файла (если файл существует)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Если dotenv не установлен, используем значения по умолчанию
    pass

# Получаем файл базы
DB_FILE = os.environ.get("DB_FILE", "anecdote_bot.db")


@contextmanager
def get_connection():
    """
    Контекстный менеджер для соединения с базой данных.

    :yields: Соединение с базой данных SQLite
    :rtype: sqlite3.Connection
    :raises sqlite3.Error: При ошибке подключения к базе данных
    """
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Ошибка базы данных: {e}")
    finally:
        conn.close()


class Database:
    """
    Класс для работы с базой данных анекдотов.

    :ivar DB_FILE: Путь к файлу базы данных
    :type DB_FILE: str
    """

    def __init__(self):
        """
        Инициализация объекта базы данных.

        :returns: Экземпляр класса Database
        :rtype: Database
        """
        self.init_db()

    def init_db(self):
        """
        Инициализация базы данных с темами.

        :raises sqlite3.Error: При ошибке создания таблиц
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Таблица пользователей
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Таблица анекдотов
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS jokes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        author_id INTEGER,
                        is_approved BOOLEAN DEFAULT 1,
                        status TEXT DEFAULT 'approved',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (author_id) REFERENCES users (id)
                    )
                    """
                )

                # Таблица тем анекдотов (5 тем)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS themes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        emoji TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Таблица связи анекдотов с темами
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS joke_themes (
                        joke_id INTEGER,
                        theme_id INTEGER,
                        weight REAL DEFAULT 1.0,
                        PRIMARY KEY (joke_id, theme_id),
                        FOREIGN KEY (joke_id) REFERENCES jokes (id),
                        FOREIGN KEY (theme_id) REFERENCES themes (id)
                    )
                    """
                )

                # Таблица предпочтений пользователей
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id INTEGER,
                        theme_id INTEGER,
                        score REAL DEFAULT 0.0,
                        interactions INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, theme_id),
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (theme_id) REFERENCES themes (id)
                    )
                    """
                )

                # Таблица взаимодействий
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        joke_id INTEGER,
                        liked BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, joke_id)
                    )
                    """
                )

                # Таблица избранного
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS favorites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        joke_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, joke_id)
                    )
                    """
                )

                # Добавляем 5 основных тем
                themes = [
                    ("Работа", "💻", "Анекдоты про работу и офис"),
                    ("Школьные", "🎓", "Анекдоты про студентов и учебу"),
                    ("Животные", "🐈", "Анекдоты про животных"),
                    (
                        "Черный юмор",
                        "🔞",
                        "Чёрный юмор — это анекдоты про то, что вызывает ужас.",
                    ),
                    ("Разное", "🎭", "Разные анекдоты"),
                ]

                cursor.executemany(
                    "INSERT OR IGNORE INTO themes (name, emoji, description) VALUES (?, ?, ?)",
                    themes,
                )

                # Проверяем, есть ли анекдоты
                cursor.execute("SELECT COUNT(*) FROM jokes")
                if cursor.fetchone()[0] == 0:
                    self._add_initial_jokes(cursor)

                print("✅ База данных с темами создана успешно")

        except sqlite3.Error as e:
            print(f"❌ Ошибка инициализации БД: {e}")

    def _add_initial_jokes(self, cursor):
        """
        Добавить начальные анекдоты с темами.

        :param cursor: Курсор базы данных
        :type cursor: sqlite3.Cursor
        """
        jokes_with_themes = [
            {
                "text": "Доктор, я съел пиццу вместе с упаковкой. Я умру? "
                "— Ну, все когда-нибудь умрут... — Все умрут! Ужас, что я наделал!",
                "themes": [1, 2],  # Рабочие, Школьные
            },
            {
                "text": "Де и Ито давно дружат. Однажды у Ито были неприятности, "
                "но Де его выручил, Де спас Ито",
                "themes": [5],  # анекдоты на все случаи жизни
            },
            {
                "text": "На уроке русского языка учитель говорит грузину: "
                "- Скажи хлеб - Хлэб. - Мягче - Хлэп! - Еще мягче! - Буличка",
                "themes": [1, 2],  # Рабочие, Школьные
            },
        ]

        for joke_data in jokes_with_themes:
            cursor.execute(
                "INSERT INTO jokes (text) VALUES (?)", (joke_data["text"],)
            )
            joke_id = cursor.lastrowid

            # Добавляем связи с темами
            for theme_id in joke_data["themes"]:
                cursor.execute(
                    "INSERT INTO joke_themes (joke_id, theme_id) VALUES (?, ?)",
                    (joke_id, theme_id),
                )

        print(f"✅ Добавлено {len(jokes_with_themes)} начальных анекдотов с темами")

    def get_or_create_user(self, telegram_id, username, first_name, last_name):
        """
        Получить или создать пользователя.

        :param telegram_id: Уникальный идентификатор пользователя в Telegram
        :type telegram_id: int
        :param username: Имя пользователя в Telegram
        :type username: str or None
        :param first_name: Имя пользователя
        :type first_name: str
        :param last_name: Фамилия пользователя
        :type last_name: str or None
        :returns: Словарь с данными пользователя
        :rtype: dict
        :raises sqlite3.Error: При ошибке работы с базой данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT id FROM users WHERE telegram_id = ?",
                    (telegram_id,),
                )
                row = cursor.fetchone()

                if row:
                    return {
                        "id": row["id"],
                        "telegram_id": telegram_id,
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                    }

                cursor.execute(
                    """
                    INSERT INTO users 
                    (telegram_id, username, first_name, last_name) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (telegram_id, username, first_name, last_name),
                )
                user_id = cursor.lastrowid

                # Создаем начальные предпочтения для новых пользователей
                for theme_id in range(1, 6):  # 5 тем
                    cursor.execute(
                        """
                        INSERT INTO user_preferences 
                        (user_id, theme_id, score) 
                        VALUES (?, ?, 0.0)
                        """,
                        (user_id, theme_id),
                    )

                print(f"✅ Создан пользователь: {first_name} (ID: {user_id})")

                return {
                    "id": user_id,
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                }

        except sqlite3.Error as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            return {
                "id": telegram_id,
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }

    def get_random_joke(self, excluded_ids=None, theme_id=None):
        """
        Получить случайный одобренный анекдот.

        :param excluded_ids: Список ID анекдотов для исключения
        :type excluded_ids: list or tuple or set or None
        :param theme_id: ID темы для фильтрации
        :type theme_id: int or None
        :returns: Словарь с анекдотом или None
        :rtype: dict or None
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                if theme_id:
                    query = """
                        SELECT j.id, j.text 
                        FROM jokes j
                        JOIN joke_themes jt ON j.id = jt.joke_id
                        WHERE j.is_approved = 1 AND jt.theme_id = ?
                    """
                    params = [theme_id]
                else:
                    query = "SELECT id, text FROM jokes WHERE is_approved = 1"
                    params = []

                if excluded_ids:
                    if isinstance(excluded_ids, (list, tuple, set)):
                        if excluded_ids:
                            ids_str = ",".join(str(id) for id in excluded_ids)
                            query += f" AND j.id NOT IN ({ids_str})"

                query += " ORDER BY RANDOM() LIMIT 1"
                cursor.execute(query, params)
                row = cursor.fetchone()

                if row:
                    return {"id": row["id"], "text": row["text"]}

                return None

        except sqlite3.Error as e:
            print(f"❌ Ошибка получения анекдота: {e}")
            return None

    def get_joke_themes(self, joke_id):
        """
        Получить темы анекдота.

        :param joke_id: ID анекдота
        :type joke_id: int
        :returns: Список тем анекдота
        :rtype: list
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.emoji, jt.weight
                    FROM themes t
                    JOIN joke_themes jt ON t.id = jt.theme_id
                    WHERE jt.joke_id = ?
                    """,
                    (joke_id,),
                )

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Ошибка получения тем анекдота: {e}")
            return []

    def classify_joke(self, joke_text):
        """
        Определить темы анекдота по тексту.

        :param joke_text: Текст анекдота
        :type joke_text: str
        :returns: Список ID тем анекдота
        :rtype: list
        """
        keywords = {
            1: [
                "работа",
                "офис",
                "начальник",
                "коллега",
                "зарплата",
                "совещание",
                "отчет",
                "дедлайн",
            ],
            2: [
                "студент",
                "универ",
                "сессия",
                "экзамен",
                "зачет",
                "препод",
                "лекция",
                "институт",
                "общежитие",
            ],
            3: [
                "кот",
                "собака",
                "мышь",
                "медведь",
                "съел",
                "поймал",
                "корова",
                "попугай",
            ],
            4: ["смерть", "умер", "Штирлиц", "Мюллер", "бар", "проститутка", "негр"],
            5: [],  # Разное - по умолчанию
        }

        joke_text_lower = joke_text.lower()
        themes = []

        for theme_id, words in keywords.items():
            if any(word in joke_text_lower for word in words):
                themes.append(theme_id)

        # Если не нашли тем, добавляем в "Разное"
        if not themes:
            themes = [5]

        return themes

    def add_user_joke(self, text, author_id):
        """
        Добавить анекдот от пользователя (на модерацию).

        :param text: Текст анекдота
        :type text: str
        :param author_id: ID автора анекдота
        :type author_id: int
        :returns: Информация о добавленном анекдоте или None
        :rtype: dict or None
        :raises sqlite3.Error: При ошибке добавления в базу данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO jokes 
                    (text, author_id, is_approved, status) 
                    VALUES (?, ?, 0, 'pending')
                    """,
                    (text, author_id),
                )
                joke_id = cursor.lastrowid

                # Классифицируем анекдот и добавляем темы
                themes = self.classify_joke(text)
                for theme_id in themes:
                    cursor.execute(
                        "INSERT INTO joke_themes (joke_id, theme_id) VALUES (?, ?)",
                        (joke_id, theme_id),
                    )

                print(
                    f"✅ Пользовательский анекдот добавлен: ID={joke_id}, Темы={themes}"
                )

                return {
                    "joke_id": joke_id,
                    "author_username": "user",
                    "author_name": "Пользователь",
                }

        except sqlite3.Error as e:
            print(f"❌ Ошибка добавления анекдота: {e}")
            return None

    def get_user_preferences(self, user_id):
        """
        Получить предпочтения пользователя по темам.

        :param user_id: ID пользователя
        :type user_id: int
        :returns: Словарь предпочтений пользователя
        :rtype: dict
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.emoji, up.score, up.interactions
                    FROM themes t
                    LEFT JOIN user_preferences up ON t.id = up.theme_id AND up.user_id = ?
                    ORDER BY t.id
                    """,
                    (user_id,),
                )

                preferences = {}
                for row in cursor.fetchall():
                    preferences[row["id"]] = {
                        "name": row["name"],
                        "emoji": row["emoji"],
                        "score": row["score"] or 0.0,
                        "interactions": row["interactions"] or 0,
                    }
                return preferences
        except sqlite3.Error as e:
            print(f"❌ Ошибка получения предпочтений: {e}")
            return {}

    def _update_single_theme_preference(self, cursor, user_id, theme, liked):
        """
        Обновить предпочтение для одной темы.

        :param cursor: Курсор базы данных
        :type cursor: sqlite3.Cursor
        :param user_id: ID пользователя
        :type user_id: int
        :param theme: Данные темы
        :type theme: dict
        :param liked: Оценка пользователя (нравится/не нравится)
        :type liked: bool
        """
        theme_id = theme["id"]
        weight = theme["weight"] or 1.0

        # Получаем текущую оценку
        cursor.execute(
            """
            SELECT score FROM user_preferences 
            WHERE user_id = ? AND theme_id = ?
            """,
            (user_id, theme_id),
        )
        row = cursor.fetchone()

        current_score = row["score"] if row else 0.0

        # Обновляем оценку
        delta = 0.1 * weight
        if liked:
            new_score = min(1.0, current_score + delta)
        else:
            new_score = max(-1.0, current_score - delta)

        # Обновляем в базе
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences 
            (user_id, theme_id, score, interactions, last_updated)
            VALUES (?, ?, ?, COALESCE(
                (SELECT interactions + 1 FROM user_preferences 
                 WHERE user_id = ? AND theme_id = ?), 1
            ), CURRENT_TIMESTAMP)
            """,
            (user_id, theme_id, new_score, user_id, theme_id),
        )

    def update_user_preference(self, user_id, joke_id, liked):
        """
        Обновить предпочтения пользователя на основе оценки анекдота.

        :param user_id: ID пользователя
        :type user_id: int
        :param joke_id: ID анекдота
        :type joke_id: int
        :param liked: Оценка пользователя (нравится/не нравится)
        :type liked: bool
        :returns: Флаг успешного обновления
        :rtype: bool
        :raises sqlite3.Error: При ошибке обновления базы данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Получаем темы анекдота
                themes = self.get_joke_themes(joke_id)
                if not themes:
                    return False

                for theme in themes:
                    self._update_single_theme_preference(
                        cursor, user_id, theme, liked
                    )

                return True

        except sqlite3.Error as e:
            print(f"❌ Ошибка обновления предпочтений: {e}")
            return False

    def get_user_interactions(self, user_id):
        """
        Получить взаимодействия пользователя.

        :param user_id: ID пользователя
        :type user_id: int
        :returns: Список ID анекдотов, с которыми взаимодействовал пользователь
        :rtype: list
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT joke_id FROM interactions WHERE user_id = ?",
                    (user_id,),
                )
                return [row["joke_id"] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"❌ Ошибка получения взаимодействий: {e}")
            return []

    def add_interaction(self, user_id, joke_id, liked):
        """
        Добавить взаимодействие.

        :param user_id: ID пользователя
        :type user_id: int
        :param joke_id: ID анекдота
        :type joke_id: int
        :param liked: Оценка пользователя (нравится/не нравится)
        :type liked: bool
        :returns: Флаг успешного добавления
        :rtype: bool
        :raises sqlite3.Error: При ошибке добавления в базу данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO interactions 
                    (user_id, joke_id, liked) 
                    VALUES (?, ?, ?)
                    """,
                    (user_id, joke_id, liked),
                )
                return True
        except sqlite3.Error as e:
            print(f"❌ Ошибка добавления взаимодействия: {e}")
            return False

    def add_favorite(self, user_id, joke_id):
        """
        Добавить анекдот в избранное.

        :param user_id: ID пользователя
        :type user_id: int
        :param joke_id: ID анекдота
        :type joke_id: int
        :returns: Кортеж (успех, сообщение)
        :rtype: tuple
        :raises sqlite3.Error: При ошибке работы с базой данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM favorites WHERE user_id = ? AND joke_id = ?",
                    (user_id, joke_id),
                )

                if cursor.fetchone():
                    cursor.execute(
                        "DELETE FROM favorites WHERE user_id = ? AND joke_id = ?",
                        (user_id, joke_id),
                    )
                    return False, "❌ Удалено из избранного"

                cursor.execute(
                    "INSERT INTO favorites (user_id, joke_id) VALUES (?, ?)",
                    (user_id, joke_id),
                )
                return True, "⭐ Добавлено в избранное"

        except sqlite3.Error as e:
            print(f"❌ Ошибка избранного: {e}")
            return False, "❌ Ошибка"

    def get_user_favorites(self, user_id):
        """
        Получить избранные анекдоты пользователя.

        :param user_id: ID пользователя
        :type user_id: int
        :returns: Список избранных анекдотов
        :rtype: list
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT j.id, j.text 
                    FROM jokes j
                    JOIN favorites f ON j.id = f.joke_id
                    WHERE f.user_id = ? AND j.is_approved = 1
                    ORDER BY f.created_at DESC
                    """,
                    (user_id,),
                )

                return [
                    {"id": row["id"], "text": row["text"]}
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            print(f"❌ Ошибка получения избранного: {e}")
            return []

    def get_user_jokes(self, user_id, status=None):
        """
        Получить анекдоты пользователя.

        :param user_id: ID пользователя
        :type user_id: int
        :param status: Статус анекдота для фильтрации
        :type status: str or None
        :returns: Список анекдотов пользователя
        :rtype: list
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT id, text, is_approved, status, created_at 
                    FROM jokes 
                    WHERE author_id = ?
                """
                params = [user_id]

                if status:
                    query += " AND status = ?"
                    params.append(status)

                query += " ORDER BY created_at DESC"
                cursor.execute(query, params)

                jokes = []
                for row in cursor.fetchall():
                    status_emoji = {
                        "approved": "✅",
                        "pending": "⏳",
                        "rejected": "❌",
                    }.get(row["status"], "❓")

                    jokes.append(
                        {
                            "id": row["id"],
                            "text": row["text"],
                            "status": row["status"],
                            "status_emoji": status_emoji,
                            "is_approved": bool(row["is_approved"]),
                            "created_at": row["created_at"],
                        }
                    )

                return jokes

        except sqlite3.Error as e:
            print(f"❌ Ошибка получения анекдотов пользователя: {e}")
            return []

    def get_pending_jokes_count(self):
        """
        Получить количество анекдотов на модерации.

        :returns: Количество анекдотов на модерации
        :rtype: int
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM jokes WHERE status = 'pending'"
                )
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"❌ Ошибка получения счетчика: {e}")
            return 0

    def get_themes_statistics(self):
        """
        Получить статистику по темам.

        :returns: Статистика по темам
        :rtype: list
        :raises sqlite3.Error: При ошибке запроса к базе данных
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT t.id, t.name, COUNT(jt.joke_id) as count
                    FROM themes t
                    LEFT JOIN joke_themes jt ON t.id = jt.theme_id
                    GROUP BY t.id
                    """
                )

                stats = []
                for row in cursor.fetchall():
                    cursor.execute(
                        """
                        SELECT COUNT(DISTINCT jt.joke_id) as approved_count
                        FROM joke_themes jt
                        JOIN jokes j ON jt.joke_id = j.id
                        WHERE jt.theme_id = ? AND j.is_approved = 1
                        """,
                        (row["id"],),
                    )

                    approved_row = cursor.fetchone()
                    approved_count = (
                        approved_row["approved_count"] if approved_row else 0
                    )

                    stats.append(
                        {
                            "name": row["name"],
                            "total": row["count"],
                            "approved": approved_count,
                        }
                    )

                return stats
        except sqlite3.Error as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return []


# Создаем глобальный объект
db = Database()
