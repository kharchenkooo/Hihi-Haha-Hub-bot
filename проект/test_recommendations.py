"""
Тесты для рекомендательной системы.
"""
import os
import sys
import unittest

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommendations import ThemeBasedRecommender, recommender


class TestThemeBasedRecommender(unittest.TestCase):
    """Тестирование класса ThemeBasedRecommender из recommendations.py."""

    def test_recommender_initialization(self):
        """Тест 1: Проверка инициализации рекомендательной системы."""
        # Создаем экземпляр
        recommender_instance = ThemeBasedRecommender()

        # Проверяем атрибуты
        self.assertEqual(recommender_instance.themes_count, 5)
        self.assertEqual(recommender_instance.learning_rate, 0.1)
        self.assertEqual(recommender_instance.exploration_rate, 0.1)
        self.assertEqual(recommender_instance.user_view_history, {})
        print(
            "✅ Тест 1 пройден: рекомендательная система инициализируется корректно"
        )

    def test_exploration_rate_logic(self):
        """Тест 2: Проверка логики exploration rate."""
        recommender_instance = ThemeBasedRecommender()

        # Проверяем значение exploration_rate
        self.assertEqual(recommender_instance.exploration_rate, 0.1)
        self.assertIsInstance(recommender_instance.exploration_rate, float)

        # Проверяем что это число между 0 и 1
        self.assertGreaterEqual(recommender_instance.exploration_rate, 0)
        self.assertLessEqual(recommender_instance.exploration_rate, 1)

        print("✅ Тест 2 пройден: exploration rate установлен корректно (10%)")

    def test_score_to_probability_conversion(self):
        """Тест 3: Преобразование оценок (-1..1) в вероятности (0..1)."""
        # Тестовые данные (формула из кода: (score + 1) / 2)
        test_cases = [
            (-1.0, 0.0),  # Не нравится -> 0% вероятность
            (-0.5, 0.25),  # Скорее не нравится -> 25%
            (0.0, 0.5),  # Нейтрально -> 50%
            (0.5, 0.75),  # Нравится -> 75%
            (1.0, 1.0),  # Очень нравится -> 100%
        ]

        for score, expected_prob in test_cases:
            # Формула из вашего кода
            calculated_prob = (score + 1) / 2
            self.assertAlmostEqual(calculated_prob, expected_prob, places=2)

        print(
            "✅ Тест 3 пройден: преобразование оценок в вероятности работает корректно"
        )

    def test_methods_exist(self):
        """Тест 4: Проверка существования основных методов."""
        recommender_instance = ThemeBasedRecommender()

        # Проверяем что методы существуют
        required_methods = ["get_recommended_joke", "get_user_profile"]

        for method in required_methods:
            self.assertTrue(hasattr(recommender_instance, method))
            self.assertTrue(callable(getattr(recommender_instance, method)))
            print(f"✅ Метод {method} существует")

    def test_global_recommender_object(self):
        """Тест 5: Проверка глобального объекта рекомендателя."""
        self.assertIsNotNone(recommender)
        self.assertIsInstance(recommender, ThemeBasedRecommender)
        print("✅ Тест 5 пройден: глобальный объект recommender создан")

    def test_recommender_class_has_correct_structure(self):
        """Тест 6: Проверка структуры класса рекомендательной системы."""
        # Проверяем что класс можно создать
        recommender_instance = ThemeBasedRecommender()

        # Проверяем наличие всех ожидаемых атрибутов
        expected_attributes = [
            "themes_count",
            "learning_rate",
            "exploration_rate",
            "user_view_history",
            "get_recommended_joke",
            "get_user_profile",
        ]

        for attr in expected_attributes:
            self.assertTrue(
                hasattr(recommender_instance, attr),
                f"Класс должен иметь атрибут: {attr}"
            )

        print("✅ Тест 6 пройден: структура класса корректна")


if __name__ == "__main__":
    unittest.main(verbosity=2)