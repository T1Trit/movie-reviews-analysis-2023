"""
Обработчики команд анализа фильмов.
Команды для поиска, анализа и получения информации о фильмах.
"""

import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from loguru import logger

# Импорт сервисов
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_config
from bot.services.sentiment_service import get_sentiment_service
from bot.services.visualization_service import get_visualization_service

# Создание роутера
analysis_router = Router()

@analysis_router.message(Command("search"))
async def cmd_search(message: Message):
    """Команда поиска фильмов."""
    # Извлечение названия фильма из команды
    command_text = message.text
    if not command_text or len(command_text.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\\n\\n"
            "Используйте: /search <название фильма>\\n"
            "Пример: /search Оппенгеймер"
        )
        return
    
    movie_name = " ".join(command_text.split()[1:])
    logger.info(f"Поиск фильма: {movie_name}")
    
    # Отправка сообщения о поиске
    search_msg = await message.answer(f"🔍 Ищу фильм: <b>{movie_name}</b>...")
    
    try:
        # Здесь будет реальный поиск через API Кинопоиска
        # Пока используем заглушку с тестовыми данными
        search_results = await mock_search_movies(movie_name)
        
        if not search_results:
            await search_msg.edit_text(
                f"😔 Фильм <b>{movie_name}</b> не найден.\\n\\n"
                "💡 Попробуйте:\\n"
                "• Проверить правописание\\n"
                "• Использовать английское название\\n"
                "• Указать год выпуска"
            )
            return
        
        # Формирование результатов поиска
        if len(search_results) == 1:
            movie = search_results[0]
            result_text = format_single_movie_result(movie)
            keyboard = create_movie_action_keyboard(movie['id'])
        else:
            result_text = format_multiple_movies_result(search_results, movie_name)
            keyboard = None
        
        await search_msg.edit_text(result_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка поиска фильма {movie_name}: {e}")
        await search_msg.edit_text(
            "❌ Произошла ошибка при поиске.\\n"
            "Попробуйте позже или обратитесь к администратору."
        )

@analysis_router.message(Command("analyze"))
async def cmd_analyze(message: Message):
    """Команда анализа отзывов фильма."""
    # Извлечение ID фильма
    command_text = message.text
    if not command_text or len(command_text.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\\n\\n"
            "Используйте: /analyze <ID фильма>\\n"
            "Пример: /analyze 1318972\\n\\n"
            "Найти ID фильма: /search название"
        )
        return
    
    try:
        movie_id = int(command_text.split()[1])
    except ValueError:
        await message.answer(
            "❌ <b>Неверный ID фильма</b>\\n\\n"
            "ID должен быть числом.\\n"
            "Пример: /analyze 1318972"
        )
        return
    
    logger.info(f"Анализ фильма ID: {movie_id}")
    
    # Сообщение о начале анализа
    analysis_msg = await message.answer(
        f"📊 <b>Анализ фильма ID: {movie_id}</b>\\n\\n"
        "⏳ Загружаю данные и анализирую отзывы...\\n"
        "<i>Это может занять 10-30 секунд</i>"
    )
    
    try:
        config = get_config()
        sentiment_service = get_sentiment_service(config)
        
        # Получение анализа
        movie_analysis = sentiment_service.get_movie_sentiment_stats(movie_id)
        
        if not movie_analysis:
            await analysis_msg.edit_text(
                f"😔 <b>Данные для фильма ID: {movie_id} не найдены</b>\\n\\n"
                "💡 Возможные причины:\\n"
                "• Фильм отсутствует в базе данных\\n"
                "• Неверный ID фильма\\n"
                "• Нет отзывов для анализа\\n\\n"
                "Попробуйте найти фильм: /search название"
            )
            return
        
        # Формирование результата анализа
        analysis_text = sentiment_service.format_sentiment_summary(movie_id)
        
        # Создание кнопок для дополнительных действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Графики", 
                    callback_data=f"charts_{movie_id}"
                ),
                InlineKeyboardButton(
                    text="☁️ Облако слов", 
                    callback_data=f"wordcloud_{movie_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Сводный анализ", 
                    callback_data=f"summary_{movie_id}"
                )
            ]
        ])
        
        await analysis_msg.edit_text(analysis_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка анализа фильма {movie_id}: {e}")
        await analysis_msg.edit_text(
            "❌ Произошла ошибка при анализе.\\n"
            "Попробуйте позже или проверьте ID фильма."
        )

@analysis_router.message(Command("movie"))
async def cmd_movie_info(message: Message):
    """Получение подробной информации о фильме."""
    command_text = message.text
    if not command_text or len(command_text.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\\n\\n"
            "Используйте: /movie <ID фильма>\\n"
            "Пример: /movie 1318972"
        )
        return
    
    try:
        movie_id = int(command_text.split()[1])
    except ValueError:
        await message.answer("❌ ID фильма должен быть числом")
        return
    
    logger.info(f"Запрос информации о фильме ID: {movie_id}")
    
    info_msg = await message.answer(f"🎬 Получаю информацию о фильме ID: {movie_id}...")
    
    try:
        # Здесь будет запрос к API Кинопоиска для получения информации
        movie_info = await mock_get_movie_info(movie_id)
        
        if not movie_info:
            await info_msg.edit_text(
                f"😔 Информация о фильме ID: {movie_id} не найдена"
            )
            return
        
        # Формирование информации о фильме
        info_text = format_movie_info(movie_info)
        
        # Кнопки для дальнейших действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Анализировать отзывы", 
                    callback_data=f"analyze_{movie_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Графики", 
                    callback_data=f"charts_{movie_id}"
                ),
                InlineKeyboardButton(
                    text="☁️ Облако слов", 
                    callback_data=f"wordcloud_{movie_id}"
                )
            ]
        ])
        
        await info_msg.edit_text(info_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о фильме {movie_id}: {e}")
        await info_msg.edit_text("❌ Ошибка получения информации о фильме")

# Обработчики inline кнопок
@analysis_router.callback_query(F.data.startswith("analyze_"))
async def callback_analyze(callback):
    """Callback для анализа фильма."""
    movie_id = callback.data.split("_")[1]
    await callback.message.edit_text(
        f"📊 Запустите анализ командой:\\n/analyze {movie_id}",
        reply_markup=None
    )
    await callback.answer()

@analysis_router.callback_query(F.data.startswith("charts_"))
async def callback_charts(callback):
    """Callback для создания графиков."""
    movie_id = callback.data.split("_")[1]
    
    # Создание меню выбора типа графика
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="😊 Настроения", 
                callback_data=f"chart_{movie_id}_sentiment"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ Рейтинги", 
                callback_data=f"chart_{movie_id}_ratings"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Сводный анализ", 
                callback_data=f"chart_{movie_id}_summary"
            )
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_analyze_{movie_id}")
        ]
    ])
    
    await callback.message.edit_text(
        f"📊 <b>Выберите тип графика для фильма ID: {movie_id}</b>",
        reply_markup=keyboard
    )
    await callback.answer()

@analysis_router.callback_query(F.data.startswith("wordcloud_"))
async def callback_wordcloud(callback):
    """Callback для создания облака слов."""
    movie_id = int(callback.data.split("_")[1])
    
    await callback.message.edit_text(
        f"☁️ Создаю облако слов для фильма ID: {movie_id}...\\n"
        "<i>Это может занять несколько секунд</i>"
    )
    
    try:
        config = get_config()
        sentiment_service = get_sentiment_service(config)
        viz_service = get_visualization_service(config)
        
        # Получение данных фильма
        movie_analysis = sentiment_service.get_movie_sentiment_stats(movie_id)
        
        if not movie_analysis:
            await callback.message.edit_text(
                f"😔 Данные для создания облака слов не найдены\\n"
                f"ID фильма: {movie_id}"
            )
            await callback.answer()
            return
        
        # Создание облака слов
        wordcloud_buffer = viz_service.create_wordcloud(
            movie_analysis.reviews_sample, 
            movie_analysis.movie_title
        )
        
        if wordcloud_buffer:
            # Отправка изображения
            photo = BufferedInputFile(
                wordcloud_buffer.read(),
                filename=f"wordcloud_{movie_id}.png"
            )
            
            await callback.message.answer_photo(
                photo=photo,
                caption=f"☁️ <b>Облако слов: {movie_analysis.movie_title}</b>\\n"
                       f"📝 Основано на {movie_analysis.total_reviews} отзывах"
            )
            
            await callback.message.edit_text(
                "✅ Облако слов создано и отправлено выше"
            )
        else:
            await callback.message.edit_text(
                "❌ Не удалось создать облако слов\\n"
                "Возможно, недостаточно текстовых данных"
            )
    
    except Exception as e:
        logger.error(f"Ошибка создания облака слов для {movie_id}: {e}")
        await callback.message.edit_text(
            "❌ Ошибка создания облака слов"
        )
    
    await callback.answer()

# Вспомогательные функции (заглушки для демонстрации)

async def mock_search_movies(query: str) -> list:
    """Заглушка для поиска фильмов."""
    # Симуляция задержки API
    await asyncio.sleep(1)
    
    # Тестовые данные
    test_movies = {
        "оппенгеймер": [
            {
                "id": 1318972,
                "title": "Оппенгеймер",
                "original_title": "Oppenheimer",
                "year": 2023,
                "rating": 8.2,
                "genres": ["драма", "биография", "история"],
                "description": "Биографический триллер о жизни физика Роберта Оппенгеймера"
            }
        ],
        "барби": [
            {
                "id": 1202258,
                "title": "Барби",
                "original_title": "Barbie",
                "year": 2023,
                "rating": 7.1,
                "genres": ["комедия", "фэнтези"],
                "description": "Кукла Барби отправляется в реальный мир"
            }
        ],
        "человек-паук": [
            {
                "id": 1143242,
                "title": "Человек-паук: Паутина вселенных",
                "original_title": "Spider-Man: Across the Spider-Verse", 
                "year": 2023,
                "rating": 8.5,
                "genres": ["мультфильм", "фантастика", "боевик"],
                "description": "Продолжение анимационных приключений Майлза Моралеса"
            }
        ]
    }
    
    query_lower = query.lower()
    for key, movies in test_movies.items():
        if key in query_lower:
            return movies
    
    return []

async def mock_get_movie_info(movie_id: int) -> dict:
    """Заглушка для получения информации о фильме."""
    await asyncio.sleep(1)
    
    test_info = {
        1318972: {
            "id": 1318972,
            "title": "Оппенгеймер",
            "original_title": "Oppenheimer",
            "year": 2023,
            "rating": 8.2,
            "duration": 180,
            "genres": ["драма", "биография", "история"],
            "country": ["США"],
            "director": "Кристофер Нолан",
            "description": "Биографический триллер о жизни физика Роберта Оппенгеймера, руководившего созданием атомной бомбы."
        },
        1202258: {
            "id": 1202258,
            "title": "Барби",
            "original_title": "Barbie",
            "year": 2023,
            "rating": 7.1,
            "duration": 114,
            "genres": ["комедия", "фэнтези"],
            "country": ["США"],
            "director": "Грета Гервиг",
            "description": "Кукла Барби отправляется в реальный мир, чтобы найти настоящее счастье."
        }
    }
    
    return test_info.get(movie_id)

def format_single_movie_result(movie: dict) -> str:
    """Форматирование результата одного фильма."""
    return f"""🎬 <b>Фильм найден!</b>

<b>{movie['title']}</b> ({movie['original_title']})
📅 {movie['year']} • ⭐ {movie['rating']}/10
🎭 {', '.join(movie['genres'])}
📖 {movie['description']}

🆔 ID: {movie['id']}"""

def format_multiple_movies_result(movies: list, query: str) -> str:
    """Форматирование результатов нескольких фильмов."""
    result = f"🔍 <b>Результаты поиска: {query}</b>\\n\\n"
    
    for i, movie in enumerate(movies[:5], 1):  # Максимум 5 результатов
        result += f"{i}. <b>{movie['title']}</b> ({movie['original_title']})\\n"
        result += f"📅 {movie['year']} • ⭐ {movie['rating']}/10\\n"
        result += f"🎭 {', '.join(movie['genres'])}\\n"
        result += f"🆔 ID: {movie['id']}\\n\\n"
    
    result += "💡 Для анализа используйте: /analyze ID"
    return result

def format_movie_info(movie: dict) -> str:
    """Форматирование подробной информации о фильме."""
    return f"""🎬 <b>{movie['title']}</b>

📌 <b>Оригинальное название:</b> {movie['original_title']}
📅 <b>Год:</b> {movie['year']}
⭐ <b>Рейтинг:</b> {movie['rating']}/10
⏱ <b>Длительность:</b> {movie['duration']} мин
🎭 <b>Жанры:</b> {', '.join(movie['genres'])}
🌍 <b>Страна:</b> {', '.join(movie['country'])}
🎬 <b>Режиссёр:</b> {movie['director']}

📖 <b>Описание:</b>
{movie['description']}

🆔 <b>ID для анализа:</b> {movie['id']}"""

def create_movie_action_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    """Создание клавиатуры действий для фильма."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Анализировать отзывы", 
                callback_data=f"analyze_{movie_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Графики", 
                callback_data=f"charts_{movie_id}"
            ),
            InlineKeyboardButton(
                text="ℹ️ Подробнее", 
                callback_data=f"info_{movie_id}"
            )
        ]
    ])