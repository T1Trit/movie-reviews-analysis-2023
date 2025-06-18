"""
Основные обработчики команд Telegram бота.
Команды приветствия, помощи и статуса.
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart
from loguru import logger

# Импорт конфигурации и сервисов
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_config
from bot.services.sentiment_service import get_sentiment_service

# Создание роутера
basic_router = Router()

@basic_router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    
    logger.info(f"Пользователь {user_id} ({user_name}) запустил бота")
    
    welcome_text = f"""🎬 <b>Добро пожаловать, {user_name}!</b>

Это бот для анализа отзывов о фильмах с сайта Кинопоиск.

<b>🔥 Возможности:</b>
• 🔍 Поиск фильмов по названию
• 📊 Анализ настроений отзывов
• 📈 Создание графиков и диаграмм
• ☁️ Генерация облаков слов
• 📋 Подробная статистика

<b>🚀 Быстрый старт:</b>
/help - Полный список команд
/demo - Демонстрация на примере

<i>Проект основан на анализе отзывов фильмов 2023 года</i>"""

    # Создание inline-кнопок для быстрого доступа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📖 Помощь", callback_data="help"),
            InlineKeyboardButton(text="🎯 Демо", callback_data="demo")
        ],
        [
            InlineKeyboardButton(text="📊 Статус", callback_data="status"),
            InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about")
        ]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard)

@basic_router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    help_text = """📚 <b>Справка по командам бота</b>

<b>🔍 Основные команды:</b>
/start - Приветствие и начало работы
/help - Эта справка
/demo - Демонстрация возможностей

<b>🎬 Поиск и анализ:</b>
/search <название> - Поиск фильмов
<i>Пример: /search Оппенгеймер</i>

/analyze <ID> - Анализ отзывов фильма
<i>Пример: /analyze 1318972</i>

/movie <ID> - Информация о фильме
<i>Пример: /movie 1318972</i>

<b>📊 Визуализация:</b>
/chart <ID> <тип> - Создание графиков
• sentiment - график настроений
• ratings - распределение оценок
• summary - сводный анализ
<i>Пример: /chart 1318972 sentiment</i>

/wordcloud <ID> - Облако слов из отзывов
<i>Пример: /wordcloud 1318972</i>

<b>📈 Статистика:</b>
/stats - Статистика использования бота
/status - Техническое состояние

<b>ℹ️ Информация:</b>
/about - О проекте и авторах

<b>🎯 Готовые примеры для тестирования:</b>
• Оппенгеймер - ID: 1318972
• Барби - ID: 1202258
• Человек-паук - ID: 1143242

<i>💡 Совет: Начните с /demo для знакомства с возможностями!</i>"""

    await message.answer(help_text)

@basic_router.message(Command("demo"))
async def cmd_demo(message: Message):
    """Демонстрация возможностей бота."""
    demo_text = """🎯 <b>Демонстрация возможностей бота</b>

Давайте проведем анализ на примере фильма "Оппенгеймер" (2023):

<b>🔍 Что мы можем проанализировать:</b>
• Настроения зрителей (позитив/негатив/нейтрал)
• Распределение оценок (1-10)
• Популярные слова в отзывах
• Временную динамику мнений

<b>📊 Доступные форматы визуализации:</b>
• Круговые диаграммы настроений
• Столбчатые графики рейтингов
• Облака слов
• Сводные дашборды

<b>🎬 Попробуйте прямо сейчас:</b>"""

    # Кнопки для демонстрации
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Анализ: Оппенгеймер", 
                callback_data="demo_analyze_1318972"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 График настроений", 
                callback_data="demo_chart_1318972_sentiment"
            ),
            InlineKeyboardButton(
                text="☁️ Облако слов", 
                callback_data="demo_wordcloud_1318972"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎬 Другие фильмы", 
                callback_data="demo_other_movies"
            )
        ]
    ])
    
    await message.answer(demo_text, reply_markup=keyboard)

@basic_router.message(Command("status"))
async def cmd_status(message: Message):
    """Статус системы и интеграции."""
    config = get_config()
    sentiment_service = get_sentiment_service(config)
    
    # Проверка загрузки данных
    data_status = "✅ Загружены" if sentiment_service.load_existing_data() else "⚠️ Не найдены"
    
    # Проверка интеграции с проектом
    project_files_exist = all([
        config.project_root.exists(),
        (config.project_root / "data").exists(),
        (config.project_root / "notebooks").exists(),
        (config.project_root / "app").exists()
    ])
    
    integration_status = "✅ Активна" if project_files_exist else "⚠️ Частичная"
    
    status_text = f"""📊 <b>Статус системы</b>

<b>🤖 Telegram Bot:</b>
• Версия: 1.0 (интеграция)
• Режим: {'Webhook' if config.webhook_mode else 'Long Polling'}
• Debug: {'Включен' if config.debug else 'Выключен'}
• Логирование: {config.logging.level}

<b>📂 Интеграция с проектом:</b>
• Статус: {integration_status}
• Корневая папка: {config.project_root.name}
• Существующие данные: {data_status}
• Кэширование: {'Включено' if config.cache.enabled else 'Выключено'}

<b>⚙️ Настройки анализа:</b>
• Лимит отзывов: {config.kinopoisk.max_reviews}
• Задержка запросов: {config.kinopoisk.delay}с
• Лимит в час: {config.limits.requests_per_hour}

<b>📊 Сервисы:</b>
• Анализ настроений: ✅ VADER Sentiment
• Визуализация: ✅ matplotlib + seaborn
• Облака слов: {'✅ wordcloud' if 'wordcloud' in str(sentiment_service) else '⚠️ Не доступно'}

<i>Время проверки: {message.date.strftime('%H:%M:%S')}</i>"""

    await message.answer(status_text)

@basic_router.message(Command("about"))
async def cmd_about(message: Message):
    """Информация о проекте."""
    about_text = """ℹ️ <b>О проекте</b>

<b>🎬 Анализ отзывов фильмов 2023 года</b>
Комплексный проект анализа отзывов пользователей к фильмам с сайта Кинопоиск.

<b>👥 Авторы исходного проекта:</b>
• Мекеда Богдан (ID: 466695)
• Меркушев Алексей (ID: 475164)

<b>🤖 Telegram Bot интеграция:</b>
• Полная реализация для Telegram API
• Расширенный функционал визуализации
• Система кэширования и оптимизации
• Интеграция с существующей аналитикой

<b>🛠 Технологии:</b>
• Python 3.8+ / aiogram 3.x
• VADER Sentiment Analysis
• matplotlib, seaborn, wordcloud
• pandas, numpy, scikit-learn
• SQLite + кэширование

<b>📊 Функциональность:</b>
• Анализ настроений (VADER)
• Создание визуализаций
• Интерактивные дашборды
• Облака слов
• Статистические отчеты

<b>🔗 GitHub:</b>
github.com/T1Trit/movie-reviews-analysis-2023

<b>📄 Лицензия:</b> MIT

<i>🎯 Создано с любовью к кинематографу и анализу данных!</i>"""

    await message.answer(about_text)

@basic_router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика использования бота."""
    # TODO: Реализовать сбор статистики
    stats_text = """📈 <b>Статистика использования</b>

<b>🤖 Общая статистика:</b>
• Активных пользователей: В разработке
• Выполнено анализов: В разработке
• Создано графиков: В разработке

<b>📊 Популярные фильмы:</b>
• Оппенгеймер (ID: 1318972)
• Барби (ID: 1202258)
• Человек-паук: Паутина вселенных (ID: 1143242)

<b>🎯 Ваша активность:</b>
• Команд выполнено: В разработке
• Анализов запущено: В разработке
• Графиков создано: В разработке

<i>💡 Полная статистика будет доступна в следующих версиях</i>"""

    await message.answer(stats_text)

# Обработчики inline кнопок
@basic_router.callback_query(F.data == "help")
async def callback_help(callback):
    """Inline кнопка помощи."""
    await callback.message.edit_text(
        "Используйте команду /help для получения подробной справки",
        reply_markup=None
    )
    await callback.answer()

@basic_router.callback_query(F.data == "demo")
async def callback_demo(callback):
    """Inline кнопка демо."""
    await callback.message.edit_text(
        "Используйте команду /demo для демонстрации возможностей",
        reply_markup=None
    )
    await callback.answer()

@basic_router.callback_query(F.data == "status")
async def callback_status(callback):
    """Inline кнопка статуса."""
    await callback.message.edit_text(
        "Используйте команду /status для проверки состояния системы",
        reply_markup=None
    )
    await callback.answer()

@basic_router.callback_query(F.data == "about")
async def callback_about(callback):
    """Inline кнопка о проекте."""
    await callback.message.edit_text(
        "Используйте команду /about для информации о проекте",
        reply_markup=None
    )
    await callback.answer()

# Обработчики демо-кнопок
@basic_router.callback_query(F.data.startswith("demo_"))
async def callback_demo_commands(callback):
    """Обработка демо-команд."""
    data = callback.data
    
    if data == "demo_analyze_1318972":
        response = "🎬 Запустите: /analyze 1318972\nДля анализа фильма 'Оппенгеймер'"
    elif data == "demo_chart_1318972_sentiment":
        response = "📊 Запустите: /chart 1318972 sentiment\nДля графика настроений"
    elif data == "demo_wordcloud_1318972":
        response = "☁️ Запустите: /wordcloud 1318972\nДля облака слов"
    elif data == "demo_other_movies":
        response = """🎬 <b>Другие доступные фильмы:</b>
        
• Барби (2023) - ID: 1202258
  /analyze 1202258
  
• Человек-паук: Паутина вселенных - ID: 1143242
  /analyze 1143242

💡 Или найдите свой фильм: /search название"""
    else:
        response = "Команда в разработке"
    
    await callback.message.edit_text(response, reply_markup=None)
    await callback.answer()

# Обработчик неизвестных команд
@basic_router.message()
async def handle_unknown(message: Message):
    """Обработчик неизвестных сообщений."""
    text = message.text.lower() if message.text else ""
    
    if any(word in text for word in ["привет", "hello", "hi", "здравствуй"]):
        await message.answer(
            "👋 Привет! Используйте /start для начала работы или /help для справки."
        )
    elif any(word in text for word in ["спасибо", "thanks", "благодарю"]):
        await message.answer("😊 Пожалуйста! Рад помочь с анализом фильмов!")
    elif any(word in text for word in ["фильм", "кино", "movie"]):
        await message.answer(
            "🎬 Для поиска фильмов используйте: /search название\n"
            "Например: /search Оппенгеймер"
        )
    else:
        await message.answer(
            "🤔 Не понимаю эту команду.\n"
            "Используйте /help для списка доступных команд."
        )