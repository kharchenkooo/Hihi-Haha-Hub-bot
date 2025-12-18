"""
Тесты для базы данных SQLite.
"""
import os
import sqlite3
import sys
import tempfile
import unittest

import database_sqlite

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestDatabaseModule(unittest.TestCase):
    """Тестирование модуля database_sqlite.py."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        # Создаем временный файл базы данных с контекстным менеджером
        with tempfile.NamedTemporaryFile(
                suffix=".db", delete=False, mode="w"
        ) as temp_file:
            self.temp_db_file = temp_file
            self.db_path = temp_file.name

        # Сохраняем оригинальное значение переменной окружения
        self.original_db_file = os.environ.get("DB_FILE")

        # Устанавливаем временный файл базы данных
        os.environ["DB_FILE"] = self.db_path

    def tearDown(self):
        """Очистка после каждого теста."""
        # Удаляем временный файл
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

        # Восстанавливаем оригинальное значение переменной окружения
        if self.original_db_file:
            os.environ["DB_FILE"] = self.original_db_file
        elif "DB_FILE" in os.environ:
            del os.environ["DB_FILE"]

    def test_get_connection_context_manager(self):
        """Тест 1: Проверка контекстного менеджера подключения."""
        # Используем контекстный менеджер
        with database_sqlite.get_connection() as conn:
            self.assertIsInstance(conn, sqlite3.Connection)
            self.assertEqual(conn.row_factory, sqlite3.Row)

        print("✅ Тест 1 пройден: контекстный менеджер подключения работает")

    def test_database_class_exists(self):
        """Тест 2: Проверка существования класса Database."""
        # Проверяем, что класс существует
        self.assertTrue(hasattr(database_sqlite, "Database"))
        self.assertTrue(callable(database_sqlite.Database))

        print("✅ Тест 2 пройден: класс Database существует")

    def test_global_db_object(self):
        """Тест 3: Проверка глобального объекта db."""
        # Проверяем, что глобальный объект создан
        self.assertTrue(hasattr(database_sqlite, "db"))
        self.assertIsNotNone(database_sqlite.db)

        print("✅ Тест 3 пройден: глобальный объект db создан")


class TestDatabaseFunctions(unittest.TestCase):
    """Тестирование функций работы с базой данных."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        # Создаем временный файл базы данных с контекстным менеджером
        with tempfile.NamedTemporaryFile(
                suffix=".db", delete=False, mode="w"
        ) as temp_file:
            self.temp_db_file = temp_file
            self.db_path = temp_file.name

        # Сохраняем оригинальное значение переменной окружения
        self.original_db_file = os.environ.get("DB_FILE")

        # Устанавливаем временный файл базы данных
        os.environ["DB_FILE"] = self.db_path

    def tearDown(self):
        """Очистка после каждого теста."""
        # Удаляем временный файл
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

        # Восстанавливаем оригинальное значение переменной окружения
        if self.original_db_file:
            os.environ["DB_FILE"] = self.original_db_file
        elif "DB_FILE" in os.environ:
            del os.environ["DB_FILE"]

    def test_classify_joke_logic(self):
        """Тест 4: Логика классификации анекдотов по ключевым словам."""
        # Создаем экземпляр для тестирования
        db_instance = database_sqlite.Database()

        # Тестируем классификацию
        test_jokes = [
            ("Коллега на работе постоянно опаздывает", [1]),  # работа
            ("Студент сдал сессию на отлично", [2]),  # студенты
            ("Кот съел всю колбасу", [3]),  # животные
            ("Анекдот про смерть и ужас", [4]),  # черный юмор
            ("Обычный анекдот без ключевых слов", [5]),  # разное
        ]

        for joke_text, expected_themes in test_jokes:
            themes = db_instance.classify_joke(joke_text)
            # Проверяем, что все ожидаемые темы есть в результате
            for expected in expected_themes:
                self.assertIn(expected, themes)

        print("✅ Тест 4 пройден: классификация анекдотов работает")

    def test_get_or_create_user(self):
        """Тест 5: Проверка создания пользователя."""
        db_instance = database_sqlite.Database()

        # Тестируем создание пользователя
        user = db_instance.get_or_create_user(
            telegram_id=12345,
            username="test",
            first_name="Test",
            last_name="User"
        )

        self.assertIsNotNone(user)
        self.assertEqual(user["telegram_id"], 12345)
        self.assertEqual(user["username"], "test")
        self.assertEqual(user["first_name"], "Test")

        print("✅ Тест 5 пройден: пользователь создается корректно")

    def test_add_and_get_interaction(self):
        """Тест 6: Проверка добавления и получения взаимодействий."""
        db_instance = database_sqlite.Database()

        # Создаем тестового пользователя
        user = db_instance.get_or_create_user(
            telegram_id=67890,
            username="test2",
            first_name="Test2",
            last_name="User2"
        )

        # Добавляем взаимодействие
        result = db_instance.add_interaction(user["id"], 1, True)
        self.assertTrue(result)

        # Получаем взаимодействия
        interactions = db_instance.get_user_interactions(user["id"])
        self.assertIn(1, interactions)

        print("✅ Тест 6 пройден: взаимодействия работают корректно")


if __name__ == "__main__":
    unittest.main(verbosity=2)