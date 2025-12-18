"""
Скрипт для запуска всех тестов проекта.
Запуск: python run_all_tests.py
"""
import os
import sys
import unittest


def run_all_tests():
    """Запуск всех тестов проекта."""
    print("=" * 60)
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ ПРОЕКТА")
    print("=" * 60)

    # Находим все тестовые файлы
    test_files = [
        "test_recommendations.py",
        "test_database.py",
        "test_bot_structure.py",
    ]

    # Проверяем существование файлов
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
        else:
            print(f"⚠️  Файл {test_file} не найден")

    if not existing_tests:
        print("❌ Тестовые файлы не найдены!")
        return False

    print(f"📁 Найдено тестовых файлов: {len(existing_tests)}")

    # Загружаем и запускаем тесты
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_file in existing_tests:
        try:
            # Загружаем тесты из файла
            module_name = test_file.replace(".py", "")
            tests = loader.loadTestsFromName(module_name)
            suite.addTests(tests)
            print(f"✅ Загружены тесты из {test_file}")
        except (ImportError, AttributeError, TypeError) as e:
            print(f"❌ Ошибка загрузки тестов из {test_file}: {e}")

    # Запускаем тесты
    print("\n" + "=" * 60)
    print("🧪 ВЫПОЛНЕНИЕ ТЕСТОВ")
    print("=" * 60)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Вывод итогов
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    successful_tests = (
        result.testsRun - len(result.failures) - len(result.errors)
    )
    print(f"✅ Успешно: {successful_tests}")
    print(f"⚠️  Провалено: {len(result.failures)}")
    print(f"❌ Ошибок: {len(result.errors)}")
    print(f"📈 Всего тестов: {result.testsRun}")

    # Проверяем соответствие критериям проекта
    print("\n" + "=" * 60)
    print("🎯 СООТВЕТСТВИЕ КРИТЕРИЯМ ПРОЕКТА")
    print("=" * 60)

    criteria = {
        "✅ В проекте есть хотя бы 1 тест": result.testsRun > 0,
        "✅ Тесты можно запустить": result.testsRun > 0,
        "✅ Проект имеет полную структуру": all(
            os.path.exists(f)
            for f in ["main.py", "database_sqlite.py", "recommendations.py"]
        ),
    }

    for criterion, status in criteria.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {criterion}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
