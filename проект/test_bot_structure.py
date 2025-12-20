"""
Тесты структуры проекта.
"""
import unittest
from pathlib import Path
import sqlite3
import random
import asyncio
from database_sqlite import Database, db
from recommendations import ThemeBasedRecommender, recommender


class TestProjectStructure(unittest.TestCase):
    """Тест структуры проекта."""

    def setUp(self):
        """Настройка перед тестами."""
        self.project_root = Path(__file__).parent
        print(f"\n📁 Корень проекта: {self.project_root}")

    def test_project_files_exist(self):
        """Тест 1: Проверка наличия основных файлов проекта."""
        required_files = [
            "main.py",  
            "database_sqlite.py",  
            "recommendations.py", 
            "test_database.py",  
            "test_recommendations.py", 
            "test_bot_structure.py",
        ]

        for file in required_files:
            file_path = self.project_root / file
            self.assertTrue(
                file_path.exists(),
                f"❌ Файл {file} не найден"
            )
            print(f"✅ Файл {file} существует")

    def test_python_files_content(self):
        """Тест 2: Проверка содержания Python файлов."""
        python_files = [
            "main.py",  # Основной файл бота
            "database_sqlite.py",  # Модуль базы данных
            "recommendations.py",  # Модуль рекомендаций
        ]

        for file in python_files:
            file_path = self.project_root / file
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertGreater(
                        len(content),
                        0,
                        f"❌ Файл {file} пустой"
                    )
                    print(
                        f"✅ Файл {file} содержит код ({len(content)} символов)"
                    )
            else:
                self.fail(f"❌ Файл {file} не найден")

    def test_imports_work(self):
        """Тест 3: Проверка базовых импортов."""
        try:
            self.assertIsNotNone(sqlite3)
            self.assertIsNotNone(random)
            self.assertIsNotNone(Path)
            self.assertIsNotNone(asyncio)

            print("✅ Базовые импорты работают")
        except ImportError as e:
            self.fail(f"❌ Ошибка импорта: {e}")

    def test_database_module_imports(self):
        """Тест 4: Проверка импорта модуля базы данных."""
        try:
            self.assertIsNotNone(Database)
            self.assertIsNotNone(db)
            print("✅ Импорт модуля базы данных успешен")

        except (ImportError, AttributeError) as e:
            self.fail(f"❌ Ошибка импорта модуля базы данных: {e}")

    def test_bot_structure(self):
        """Тест 5: Проверка структуры бота в main.py."""
        try:
            # Проверяем, что main.py существует и имеет базовую структуру
            main_path = self.project_root / "main.py"
            self.assertTrue(
                main_path.exists(),
                "❌ Файл main.py не найден"
            )

            with open(main_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверяем базовые компоненты бота
            self.assertIn("Bot", content, "❌ Бот не использует aiogram.Bot")
            self.assertIn(
                "Dispatcher",
                content,
                "❌ Бот не использует aiogram.Dispatcher"
            )
            self.assertIn(
                "from database_sqlite import db",
                content,
                "❌ Бот не импортирует базу данных",
            )

            print("✅ Структура бота в main.py корректна")

        except (FileNotFoundError, OSError, UnicodeDecodeError) as e:
            self.fail(f"❌ Ошибка проверки структуры бота: {e}")

    def test_bot_functionality(self):
        """Тест 6: Проверка функциональности бота в main.py."""
        try:
            # Проверяем, что main.py существует
            main_path = self.project_root / "main.py"
            self.assertTrue(
                main_path.exists(),
                "❌ Файл main.py не найден"
            )

            with open(main_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверяем основные функции бота
            self.assertIn(
                "def get_main_keyboard",
                content,
                "❌ Функция главного меню не найдена"
            )
            self.assertIn(
                "def get_joke_keyboard",
                content,
                "❌ Функция клавиатуры анекдотов не найдена"
            )
            self.assertIn(
                "/start",
                content,
                "❌ Обработчик команды /start не найдена"
            )
            self.assertIn(
                "🎲 Новый анекдот",
                content,
                "❌ Кнопка 'Новый анекдот' не найдена"
            )

            print("✅ Функциональность бота в main.py корректна")

        except (FileNotFoundError, OSError, UnicodeDecodeError) as e:
            self.fail(f"❌ Ошибка проверки функциональности бота: {e}")

    def test_recommendations_module_imports(self):
        """Тест 7: Проверка импорта модуля рекомендаций."""
        try:
            self.assertIsNotNone(ThemeBasedRecommender)
            self.assertIsNotNone(recommender)
            self.assertIsInstance(recommender, ThemeBasedRecommender)

            print("✅ Импорт модуля рекомендаций успешен")
        except (ImportError, AttributeError) as e:
            self.fail(f"❌ Ошибка импорта модуля рекомендаций: {e}")


if __name__ == "__main__":
    unittest.main()
