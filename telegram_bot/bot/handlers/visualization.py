"""
Обработчики команд визуализации.
Создание графиков, диаграмм и облаков слов.
"""

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
visualization_router = Router()

@visualization_router.message(Command("chart"))
async def cmd_chart(message: Message):
    """Команда создания графиков."""
    command_parts = message.text.split()
    
    if len(command_parts) < 3:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\\n\\n"
            "<b>Использование:</b> /chart <ID> <тип>\\n\\n"
            "<b>Доступные типы графиков:</b>\\n"
            "• sentiment - график настроений\\n"
            "• ratings - распределение оценок\\n"
            "• summary - сводный анализ\\n\\n"
            "<b>Примеры:</b>\\n"
            "/chart 1318972 sentiment\\n"
            "/chart 1318972 ratings\\n"
            "/chart 1318972 summary"
        )
        return
    
    try:
        movie_id = int(command_parts[1])
        chart_type = command_parts[2].lower()
    except ValueError:
        await message.answer("❌ ID фильма должен быть числом")
        return
    
    if chart_type not in ['sentiment', 'ratings', 'summary']:
        await message.answer(
            "❌ <b>Неверный тип графика</b>\\n\\n"
            "Доступные типы: sentiment, ratings, summary"
        )
        return
    
    logger.info(f"Создание графика {chart_type} для фильма {movie_id}")
    
    # Сообщение о создании графика
    chart_msg = await message.answer(
        f"📊 <b>Создание графика: {chart_type}</b>\\n"
        f"🎬 Фильм ID: {movie_id}\\n\\n"
        "⏳ Генерирую визуализацию...\\n"
        "<i>Это может занять несколько секунд</i>"
    )
    
    try:
        await create_and_send_chart(chart_msg, movie_id, chart_type)
        
    except Exception as e:
        logger.error(f"Ошибка создания графика {chart_type} для {movie_id}: {e}")
        await chart_msg.edit_text(
            f"❌ Ошибка создания графика\\n"
            f"Тип: {chart_type}, ID: {movie_id}\\n\\n"
            "Попробуйте позже или проверьте данные фильма."
        )

@visualization_router.message(Command("wordcloud"))
async def cmd_wordcloud(message: Message):
    """Команда создания облака слов."""
    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\\n\\n"
            "Используйте: /wordcloud <ID фильма>\\n"
            "Пример: /wordcloud 1318972"
        )
        return
    
    try:
        movie_id = int(command_parts[1])
    except ValueError:
        await message.answer("❌ ID фильма должен быть числом")
        return
    
    logger.info(f"Создание облака слов для фильма {movie_id}")
    
    wordcloud_msg = await message.answer(
        f"☁️ <b>Создание облака слов</b>\\n"
        f"🎬 Фильм ID: {movie_id}\\n\\n"
        "⏳ Анализирую отзывы и создаю визуализацию...\\n"
        "<i>Это может занять до 30 секунд</i>"
    )
    
    try:
        await create_and_send_wordcloud(wordcloud_msg, movie_id)
        
    except Exception as e:
        logger.error(f"Ошибка создания облака слов для {movie_id}: {e}")
        await wordcloud_msg.edit_text(
            f"❌ Ошибка создания облака слов\\n"
            f"ID фильма: {movie_id}\\n\\n"
            "Возможные причины:\\n"
            "• Недостаточно текстовых данных\\n"
            "• Отсутствуют отзывы для фильма\\n"
            "• Технические проблемы"
        )

# Обработчики callback для создания графиков
@visualization_router.callback_query(F.data.startswith("chart_"))
async def callback_chart(callback):
    """Callback для создания конкретного типа графика."""
    # Формат: chart_movieid_type
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("Ошибка формата команды")
        return
    
    movie_id = int(parts[1])
    chart_type = parts[2]
    
    await callback.message.edit_text(
        f"📊 <b>Создание графика: {chart_type}</b>\\n"
        f"🎬 Фильм ID: {movie_id}\\n\\n"
        "⏳ Генерирую визуализацию..."
    )
    
    try:
        await create_and_send_chart(callback.message, movie_id, chart_type)
    except Exception as e:
        logger.error(f"Ошибка создания графика через callback: {e}")
        await callback.message.edit_text("❌ Ошибка создания графика")
    
    await callback.answer()

# Вспомогательные функции для создания визуализаций

async def create_and_send_chart(message: Message, movie_id: int, chart_type: str):
    """Создание и отправка графика."""
    config = get_config()
    sentiment_service = get_sentiment_service(config)
    viz_service = get_visualization_service(config)
    
    # Получение данных фильма
    movie_analysis = sentiment_service.get_movie_sentiment_stats(movie_id)
    
    if not movie_analysis:
        await message.edit_text(
            f"😔 <b>Данные для создания графика не найдены</b>\\n"
            f"ID фильма: {movie_id}\\n\\n"
            "Возможные причины:\\n"
            "• Фильм отсутствует в базе данных\\n"
            "• Нет отзывов для анализа\\n"
            "• Неверный ID фильма"
        )
        return
    
    # Создание графика в зависимости от типа
    chart_buffer = None
    chart_name = ""
    
    if chart_type == "sentiment":
        # График распределения настроений
        sentiment_distribution = sentiment_service.get_sentiment_distribution(movie_id)
        if sentiment_distribution:
            chart_buffer = viz_service.create_sentiment_pie_chart(
                sentiment_distribution, 
                movie_analysis.movie_title
            )
            chart_name = "график настроений"
    
    elif chart_type == "ratings":
        # График распределения рейтингов (заглушка - нужны реальные данные)
        if hasattr(movie_analysis, 'ratings') and movie_analysis.ratings:
            chart_buffer = viz_service.create_rating_distribution(
                movie_analysis.ratings,
                movie_analysis.movie_title
            )
            chart_name = "график рейтингов"
        else:
            # Создаем график на основе sentiment scores
            chart_buffer = viz_service.create_sentiment_bar_chart(
                movie_analysis.sentiment_scores,
                movie_analysis.movie_title
            )
            chart_name = "график распределения настроений"
    
    elif chart_type == "summary":
        # Сводный дашборд
        movie_data = {
            'sentiment_distribution': sentiment_distribution := sentiment_service.get_sentiment_distribution(movie_id),
            'sentiment_scores': movie_analysis.sentiment_scores,
            'total_reviews': movie_analysis.total_reviews,
            'avg_rating': movie_analysis.avg_rating,
            'avg_sentiment': sum(movie_analysis.sentiment_scores) / len(movie_analysis.sentiment_scores) if movie_analysis.sentiment_scores else 0
        }
        
        chart_buffer = viz_service.create_summary_dashboard(
            movie_data,
            movie_analysis.movie_title
        )
        chart_name = "сводный анализ"
    
    if chart_buffer:
        # Отправка изображения
        photo = BufferedInputFile(
            chart_buffer.read(),
            filename=f"{chart_type}_{movie_id}.png"
        )
        
        caption = f"📊 <b>{chart_name.title()}: {movie_analysis.movie_title}</b>\\n"
        caption += f"📝 На основе {movie_analysis.total_reviews} отзывов\\n"
        caption += f"⭐ Средний рейтинг: {movie_analysis.avg_rating:.1f}/10"
        
        await message.answer_photo(photo=photo, caption=caption)
        
        # Обновляем исходное сообщение
        await message.edit_text(
            f"✅ <b>{chart_name.title()} создан!</b>\\n"
            f"🎬 {movie_analysis.movie_title}\\n\\n"
            "📊 График отправлен выше"
        )
        
        # Добавляем кнопки для других действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="☁️ Облако слов", 
                    callback_data=f"wordcloud_{movie_id}"
                ),
                InlineKeyboardButton(
                    text="📊 Другой график", 
                    callback_data=f"charts_{movie_id}"
                )
            ]
        ])
        
        # Отправляем новое сообщение с кнопками
        await message.answer(
            "🔄 <b>Дополнительные действия:</b>", 
            reply_markup=keyboard
        )
    else:
        await message.edit_text(
            f"❌ <b>Не удалось создать {chart_name}</b>\\n"
            f"Фильм: {movie_analysis.movie_title}\\n\\n"
            "Возможные причины:\\n"
            "• Недостаточно данных для визуализации\\n"
            "• Технические проблемы с генерацией\\n"
            "• Неподдерживаемый тип графика"
        )

async def create_and_send_wordcloud(message: Message, movie_id: int):
    """Создание и отправка облака слов."""
    config = get_config()
    sentiment_service = get_sentiment_service(config)
    viz_service = get_visualization_service(config)
    
    # Получение данных фильма
    movie_analysis = sentiment_service.get_movie_sentiment_stats(movie_id)
    
    if not movie_analysis:
        await message.edit_text(
            f"😔 <b>Данные для создания облака слов не найдены</b>\\n"
            f"ID фильма: {movie_id}"
        )
        return
    
    if not movie_analysis.reviews_sample:
        await message.edit_text(
            f"😔 <b>Отсутствуют текстовые отзывы</b>\\n"
            f"Фильм: {movie_analysis.movie_title}\\n\\n"
            "Для создания облака слов нужны текстовые отзывы"
        )
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
        
        caption = f"☁️ <b>Облако слов: {movie_analysis.movie_title}</b>\\n"
        caption += f"📝 Основано на {len(movie_analysis.reviews_sample)} отзывах\\n"
        caption += f"📊 Всего отзывов в анализе: {movie_analysis.total_reviews}"
        
        await message.answer_photo(photo=photo, caption=caption)
        
        # Обновляем исходное сообщение
        await message.edit_text(
            f"✅ <b>Облако слов создано!</b>\\n"
            f"🎬 {movie_analysis.movie_title}\\n\\n"
            "☁️ Облако слов отправлено выше"
        )
        
        # Добавляем кнопки для других действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Графики", 
                    callback_data=f"charts_{movie_id}"
                ),
                InlineKeyboardButton(
                    text="📈 Анализ", 
                    callback_data=f"analyze_{movie_id}"
                )
            ]
        ])
        
        await message.answer(
            "🔄 <b>Дополнительные действия:</b>", 
            reply_markup=keyboard
        )
    else:
        await message.edit_text(
            f"❌ <b>Не удалось создать облако слов</b>\\n"
            f"Фильм: {movie_analysis.movie_title}\\n\\n"
            "Возможные причины:\\n"
            "• Библиотека wordcloud не установлена\\n"
            "• Недостаточно уникальных слов в отзывах\\n"
            "• Технические проблемы с генерацией"
        )

# Команда для создания всех типов визуализаций сразу
@visualization_router.message(Command("visualize"))
async def cmd_visualize_all(message: Message):
    """Создание всех типов визуализации для фильма."""
    command_parts = message.text.split()
    
    if len(command_parts) < 2:
        await message.answer(
            "❌ <b>Неверный формат команды</b>\\n\\n"
            "Используйте: /visualize <ID фильма>\\n"
            "Пример: /visualize 1318972\\n\\n"
            "Эта команда создаст все доступные графики и облако слов."
        )
        return
    
    try:
        movie_id = int(command_parts[1])
    except ValueError:
        await message.answer("❌ ID фильма должен быть числом")
        return
    
    logger.info(f"Создание полной визуализации для фильма {movie_id}")
    
    # Сообщение о начале процесса
    viz_msg = await message.answer(
        f"🎨 <b>Создание полной визуализации</b>\\n"
        f"🎬 Фильм ID: {movie_id}\\n\\n"
        "⏳ Создаю все типы графиков и облако слов...\\n"
        "<i>Это может занять до 60 секунд</i>\\n\\n"
        "📊 Графики будут отправлены по мере готовности"
    )
    
    try:
        # Создаем все типы визуализации последовательно
        chart_types = ['sentiment', 'summary', 'wordcloud']
        
        for chart_type in chart_types:
            try:
                if chart_type == 'wordcloud':
                    await create_and_send_wordcloud(viz_msg, movie_id)
                else:
                    await create_and_send_chart(viz_msg, movie_id, chart_type)
                
                # Небольшая пауза между созданием графиков
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка создания {chart_type} для {movie_id}: {e}")
                await message.answer(
                    f"⚠️ Ошибка создания {chart_type}, продолжаю с другими..."
                )
        
        # Финальное сообщение
        await viz_msg.edit_text(
            f"✅ <b>Полная визуализация завершена!</b>\\n"
            f"🎬 Фильм ID: {movie_id}\\n\\n"
            "📊 Все доступные графики и облако слов созданы"
        )
        
    except Exception as e:
        logger.error(f"Ошибка полной визуализации для {movie_id}: {e}")
        await viz_msg.edit_text(
            f"❌ Ошибка создания визуализации\\n"
            f"ID фильма: {movie_id}\\n\\n"
            "Попробуйте создать графики по отдельности:\\n"
            "/chart {movie_id} sentiment\\n"
            "/wordcloud {movie_id}"
        )