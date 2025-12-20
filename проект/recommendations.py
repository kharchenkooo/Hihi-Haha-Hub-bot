"""
Модуль рекомендательной системы для бота с анекдотами.

Содержит класс ThemeBasedRecommender для персонализированных рекомендаций
на основе предпочтений пользователя по темам анекдотов.
"""
import random
import sys
import os

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ThemeBasedRecommender:
    """
    Класс рекомендательной системы на основе тем анекдотов.

    Система анализирует предпочтения пользователя по 5 темам:
    - Программисты
    - Студенты
    - Работа
    - Семья
    - Разное

    :ivar themes_count: Количество доступных тем
    :type themes_count: int
    :ivar learning_rate: Скорость обучения модели
    :type learning_rate: float
    :ivar exploration_rate: Вероятность показа случайного анекдота
    :type exploration_rate: float
    :ivar user_view_history: История просмотренных анекдотов по пользователям
    :type user_view_history: dict
    """

    def __init__(self):
        """
        Инициализация рекомендательной системы.

        :returns: Экземпляр класса ThemeBasedRecommender
        :rtype: ThemeBasedRecommender
        :raises ImportError: Если не удалось импортировать модуль базы данных
        """
        try:
            from database_sqlite import db

            self.themes_count = 5
            self.learning_rate = 0.1
            self.exploration_rate = 0.1
            self.user_view_history = {}
            self.db = db
            print("✅ Рекомендательная система инициализирована")

        except ImportError as e:
            print(f"❌ Ошибка инициализации рекомендательной системы: {e}")
            raise

    def _get_random_joke_with_exclusions(self, user_id, theme_id=None):
        """
        Получить случайный анекдот с исключением просмотренных.

        :param user_id: ID пользователя
        :type user_id: int
        :param theme_id: ID темы для фильтрации (опционально)
        :type theme_id: int or None
        :returns: Случайный анекдот или None
        :rtype: dict or None
        :raises ValueError: Если user_id некорректен
        :raises AttributeError: Если база данных не доступна
        """
        try:
            excluded_ids = list(self.user_view_history.get(user_id, []))
            return self.db.get_random_joke(
                excluded_ids=excluded_ids, theme_id=theme_id
            )

        except (ValueError, AttributeError) as e:
            print(f"❌ Ошибка получения случайного анекдота: {e}")
            return None

    def get_recommended_joke(self, user_id):
        """
        Получить рекомендованный анекдот на основе предпочтений.

        Алгоритм:
        1. Получает предпочтения пользователя
        2. С вероятностью exploration_rate показывает случайный анекдот
        3. Рассчитывает вероятности тем на основе предпочтений
        4. Выбирает тему по вероятности
        5. Ищет анекдот в выбранной теме

        :param user_id: ID пользователя для персонализации
        :type user_id: int
        :returns: Словарь с анекдотом или None
        :rtype: dict or None
        :raises ValueError: Если user_id некорректен
        :raises TypeError: Если данные предпочтений некорректны
        :raises KeyError: Если отсутствуют необходимые данные
        """
        try:
            preferences = self.db.get_user_preferences(user_id)
            if not preferences:
                msg = f"⚠️ Нет предпочтений для пользователя {user_id}"
                print(f"{msg}, возвращаю случайный анекдот")
                return self.db.get_random_joke()

            self._update_view_history(user_id)
            joke = self._try_exploration_joke(user_id)
            if joke:
                msg = (f"🎲 Показан исследовательский анекдот "
                       f"для пользователя {user_id}")
                print(msg)
                return joke

            theme_probabilities = self._calculate_theme_probabilities(
                preferences
            )

            if theme_probabilities:
                print(f"📊 Вероятности тем для пользователя {user_id}:")
                for theme_id, prob in theme_probabilities:
                    print(f"  Тема {theme_id}: {prob:.2%}")

            if not theme_probabilities:
                msg = (f"⚠️ Все вероятности нулевые для "
                       f"пользователя {user_id}")
                print(msg)
                return self._get_fallback_joke(user_id)

            chosen_theme = self._choose_theme_by_probability(
                theme_probabilities
            )
            print(f"🎯 Выбрана тема {chosen_theme} "
                  f"для пользователя {user_id}")

            joke = self._search_joke_in_theme(
                user_id, chosen_theme, preferences
            )

            if joke:
                msg = (f"✅ Найден анекдот #{joke['id']} "
                       f"в теме {chosen_theme}")
                print(msg)
                return joke

            msg = f"⚠️ Не найден анекдот в теме {chosen_theme}"
            print(msg)
            return self._get_fallback_joke(user_id)

        except (ValueError, TypeError, KeyError) as e:
            print(f"❌ Ошибка рекомендации для пользователя {user_id}: {e}")
            return self.db.get_random_joke()
        except AttributeError as e:
            print(f"❌ Ошибка базы данных при рекомендации: {e}")
            return None

    def _update_view_history(self, user_id):
        """
        Обновить историю просмотров пользователя.

        :param user_id: ID пользователя
        :type user_id: int
        :raises AttributeError: Если база данных не доступна
        """
        try:
            viewed_ids = self.db.get_user_interactions(user_id)
            if user_id not in self.user_view_history:
                self.user_view_history[user_id] = set(viewed_ids)
            else:
                self.user_view_history[user_id].update(viewed_ids)

            if len(self.user_view_history[user_id]) > 100:
                recent = list(self.user_view_history[user_id])[-50:]
                self.user_view_history[user_id] = set(recent)

        except AttributeError as e:
            print(f"❌ Ошибка обновления истории просмотров: {e}")

    def _try_exploration_joke(self, user_id):
        """
        Попробовать показать случайный анекдот для исследования.

        :param user_id: ID пользователя
        :type user_id: int
        :returns: Случайный анекдот или None
        :rtype: dict or None
        """
        if random.random() < self.exploration_rate:
            msg = (f"🔍 Исследование: показываю случайный анекдот "
                   f"пользователю {user_id}")
            print(msg)
            return self._get_random_joke_with_exclusions(user_id)
        return None

    def _get_fallback_joke(self, user_id):
        """
        Получить запасной анекдот (случайный).

        :param user_id: ID пользователя
        :type user_id: int
        :returns: Случайный анекдот или None
        :rtype: dict or None
        """
        joke = self._get_random_joke_with_exclusions(user_id)
        if joke:
            msg = (f"🔄 Запасной вариант: случайный анекдот "
                   f"#{joke['id']}")
            print(msg)
        return joke

    def _search_joke_in_theme(self, user_id, theme_id, preferences):
        """
        Найти анекдот в указанной теме.

        :param user_id: ID пользователя
        :type user_id: int
        :param theme_id: ID темы
        :type theme_id: int
        :param preferences: Предпочтения пользователя
        :type preferences: dict
        :returns: Анекдот с информацией о теме или None
        :rtype: dict or None
        """
        joke = self._get_random_joke_with_exclusions(user_id, theme_id)
        if joke and theme_id in preferences:
            joke['theme_id'] = theme_id
            joke['theme_name'] = preferences[theme_id]['name']
            joke['theme_emoji'] = preferences[theme_id]['emoji']
        return joke

    def _calculate_theme_probabilities(self, preferences):
        """
        Рассчитать вероятности тем на основе предпочтений пользователя.

        :param preferences: Предпочтения пользователя
        :type preferences: dict
        :returns: Список кортежей (theme_id, probability)
        :rtype: list
        """
        theme_probabilities = []
        for theme_id, data in preferences.items():
            probability = self._calculate_theme_probability(data)
            if probability > 0:
                theme_probabilities.append((theme_id, probability))

        return self._normalize_probabilities(theme_probabilities)

    def _calculate_theme_probability(self, theme_data):
        """
        Рассчитать вероятность для одной темы.

        :param theme_data: Данные темы
        :type theme_data: dict
        :returns: Вероятность выбора темы (0-1)
        :rtype: float
        """
        score = theme_data.get('score', 0)
        interactions = theme_data.get('interactions', 0)
        probability = (score + 1) / 2

        if interactions < 5:
            probability = max(probability, 0.3)

        if score < -0.5:
            probability *= 0.3

        return probability

    def _normalize_probabilities(self, theme_probabilities):
        """
        Нормализовать вероятности тем так, чтобы сумма была равна 1.

        :param theme_probabilities: Список вероятностей тем
        :type theme_probabilities: list
        :returns: Нормализованные вероятности
        :rtype: list
        """
        if not theme_probabilities:
            return []

        total_prob = sum(prob for _, prob in theme_probabilities)
        if total_prob > 0:
            return [
                (theme, prob / total_prob)
                for theme, prob in theme_probabilities
            ]

        return [
            (theme, 1.0 / len(theme_probabilities))
            for theme, _ in theme_probabilities
        ]

    def _choose_theme_by_probability(self, theme_probabilities):
        """
        Выбрать тему на основе вероятностей.

        :param theme_probabilities: Нормализованные вероятности
        :type theme_probabilities: list
        :returns: Выбранный ID темы
        :rtype: int
        """
        themes = [theme for theme, _ in theme_probabilities]
        weights = [prob for _, prob in theme_probabilities]

        if len(themes) > 1:
            weights = [w + random.uniform(-0.05, 0.05) for w in weights]
            weights = [max(w, 0.01) for w in weights]

        return random.choices(themes, weights=weights, k=1)[0]

    def get_user_profile(self, user_id):
        """
        Получить профиль пользователя с предпочтениями по темам.

        :param user_id: ID пользователя
        :type user_id: int
        :returns: Профиль пользователя или None
        :rtype: dict or None
        :raises ValueError: Если user_id некорректен
        :raises TypeError: Если данные предпочтений некорректны
        :raises KeyError: Если отсутствуют необходимые данные
        """
        try:
            preferences = self.db.get_user_preferences(user_id)
            if not preferences:
                print(f"⚠️ Нет предпочтений для пользователя {user_id}")
                return None

            return self._create_user_profile(preferences)

        except (ValueError, TypeError, KeyError) as e:
            print(f"❌ Ошибка получения профиля пользователя {user_id}: {e}")
            return None
        except AttributeError as e:
            print(f"❌ Ошибка базы данных при получении профиля: {e}")
            return None

    def _create_user_profile(self, preferences):
        """
        Создать профиль пользователя на основе предпочтений.

        :param preferences: Предпочтения пользователя
        :type preferences: dict
        :returns: Структура профиля пользователя
        :rtype: dict
        """
        profile = {
            'themes': [],
            'total_interactions': 0,
            'favorite_theme': None,
            'least_favorite_theme': None,
            'most_interacted_theme': None
        }

        max_score = -1
        min_score = 1
        max_interactions = -1

        for theme_id, data in preferences.items():
            theme_profile = {
                'id': theme_id,
                'name': data.get('name', 'Неизвестно'),
                'emoji': data.get('emoji', '❓'),
                'score': data.get('score', 0),
                'interactions': data.get('interactions', 0)
            }

            profile['themes'].append(theme_profile)
            profile['total_interactions'] += data.get('interactions', 0)
            score = data.get('score', 0)
            interactions = data.get('interactions', 0)

            if score > max_score:
                max_score = score
                profile['favorite_theme'] = theme_id

            if score < min_score:
                min_score = score
                profile['least_favorite_theme'] = theme_id

            if interactions > max_interactions:
                max_interactions = interactions
                profile['most_interacted_theme'] = theme_id

        profile['themes'] = sorted(
            profile['themes'], key=lambda x: x['score'], reverse=True
        )

        return profile

    def get_system_stats(self):
        """
        Получить статистику работы рекомендательной системы.

        :returns: Статистика системы
        :rtype: dict
        """
        return {
            'total_users': len(self.user_view_history),
            'exploration_rate': self.exploration_rate,
            'learning_rate': self.learning_rate,
            'themes_count': self.themes_count
        }


"""
Глобальный объект рекомендателя для использования во всем приложении.

:type: ThemeBasedRecommender
"""
recommender = ThemeBasedRecommender()