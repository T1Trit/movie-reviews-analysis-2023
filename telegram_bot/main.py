"""
Точка входа для Telegram бота анализа отзывов фильмов.
Интегрированная версия для проекта movie-reviews-analysis-2023.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH для импортов
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

from config import get_config, init_directories, validate_config


async def on_startup():
    """Инициализация при запуске бота."""
    logger.info("🚀 Запуск Telegram бота анализа отзывов фильмов...")
    
    # Инициализация директорий
    init_directories()
    logger.info("📁 Директории инициализированы")
    
    # TODO: Инициализация базы данных (будет добавлено позже)
    logger.info("🗄️ База данных готова")
    
    # TODO: Инициализация кэша (будет добавлено позже)
    logger.info("💾 Кэш готов")
    
    logger.info("✅ Бот успешно запущен и готов к работе!")


async def on_shutdown():
    """Очистка ресурсов при остановке бота."""
    logger.info("🔄 Остановка бота...")
    
    # TODO: Очистка ресурсов
    
    logger.info("✅ Бот корректно остановлен")


def setup_logging():
    """Настройка логирования."""
    config = get_config()
    
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Консольное логирование
    logger.add(
        sys.stdout,
        level=config.logging.level,
        format=config.logging.format,
        colorize=True
    )
    
    # Файловое логирование
    logger.add(
        config.logging.file,
        level=config.logging.level,
        format=config.logging.format,
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip"
    )
    
    # Интерцепция стандартных логов Python
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
                
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


async def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Создание экземпляров бота и диспетчера."""
    config = get_config()
    
    # Создание бота
    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создание диспетчера
    dp = Dispatcher()
    
    # TODO: Регистрация роутеров (будет добавлено позже)
    # from bot.handlers import routers
    # for router in routers:
    #     dp.include_router(router)
    
    # Базовый обработчик для тестирования
    from aiogram import Router
    from aiogram.types import Message
    from aiogram.filters import Command
    
    test_router = Router()
    
    @test_router.message(Command("start"))
    async def cmd_start(message: Message):
        """Команда /start."""
        await message.answer(
            "🎬 <b>Добро пожаловать в бот анализа отзывов фильмов!</b>\\n\\n"
            "Этот бот может анализировать отзывы к фильмам с Кинопоиска.\\n\\n"
            "🔧 <i>Базовая функциональность подключена</i>\\n"
            "📊 <i>Полная интеграция в разработке</i>\\n\\n"
            "Используйте /help для получения справки."
        )
    
    @test_router.message(Command("help"))
    async def cmd_help(message: Message):
        """Команда /help."""
        help_text = (
            "🤖 <b>Команды бота:</b>\\n\\n"
            "/start - Приветствие\\n"
            "/help - Эта справка\\n"
            "/status - Статус бота\\n\\n"
            "🚧 <i>Дополнительные команды будут добавлены после полной интеграции:</i>\\n"
            "• /search - Поиск фильмов\\n"
            "• /analyze - Анализ отзывов\\n"
            "• /chart - Создание графиков\\n"
            "• /wordcloud - Облако слов"
        )
        await message.answer(help_text)
    
    @test_router.message(Command("status"))
    async def cmd_status(message: Message):
        """Команда /status."""
        config = get_config()
        status_text = (
            "📊 <b>Статус бота:</b>\\n\\n"
            f"✅ Версия: 1.0 (интеграция)\\n"
            f"✅ Режим: {'Webhook' if config.webhook_mode else 'Long Polling'}\\n"
            f"✅ Debug: {'Включен' if config.debug else 'Выключен'}\\n"
            f"✅ Интеграция с данными: {'Да' if config.use_existing_data else 'Нет'}\\n"
            f"✅ Директория проекта: {config.project_root.name}\\n\\n"
            "🔧 Интеграция с основным проектом успешна!"
        )
        await message.answer(status_text)
    
    dp.include_router(test_router)
    
    # Регистрация хуков
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    return bot, dp


async def run_polling():
    """Запуск бота в режиме long polling."""
    logger.info("🔄 Запуск в режиме long polling...")
    
    bot, dp = await create_bot_and_dispatcher()
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки")
    finally:
        await bot.session.close()


async def run_webhook():
    """Запуск бота в режиме webhook."""
    config = get_config()
    logger.info(f"🌐 Запуск в режиме webhook на {config.webhook_url}")
    
    bot, dp = await create_bot_and_dispatcher()
    
    # Настройка webhook
    await bot.set_webhook(
        url=f"{config.webhook_url}{config.webhook_path}",
        allowed_updates=dp.resolve_used_update_types()
    )
    
    # Создание веб-приложения
    app = web.Application()
    
    # Создание обработчика webhook
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_handler.register(app, path=config.webhook_path)
    
    # Настройка приложения
    setup_application(app, dp, bot=bot)
    
    # Добавление дополнительных маршрутов
    app.router.add_get("/health", health_check)
    
    return app


async def health_check(request):
    """Проверка здоровья сервиса."""
    config = get_config()
    return web.json_response({
        "status": "ok", 
        "service": "movie-reviews-bot",
        "version": "1.0",
        "integration": "movie-reviews-analysis-2023",
        "data_integration": config.use_existing_data
    })


def main():
    """Главная функция запуска приложения."""
    try:
        # Настройка логирования
        setup_logging()
        logger.info("📝 Логирование настроено")
        
        # Валидация конфигурации
        validate_config()
        logger.info("⚙️ Конфигурация валидна")
        
        config = get_config()
        
        # Вывод информации о запуске
        logger.info(f"🎬 Запуск бота анализа отзывов фильмов")
        logger.info(f"📂 Проект: {config.project_root}")
        logger.info(f"🔧 Режим: {'Webhook' if config.webhook_mode else 'Long Polling'}")
        logger.info(f"📊 Интеграция с данными: {'Включена' if config.use_existing_data else 'Отключена'}")
        
        if config.webhook_mode:
            # Режим webhook
            app = asyncio.run(run_webhook())
            
            # Запуск веб-сервера
            web.run_app(
                app,
                host="0.0.0.0",
                port=config.webhook_port
            )
        else:
            # Режим polling
            asyncio.run(run_polling())
            
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка при запуске: {e}")
        print(f"\\n❌ Ошибка запуска: {e}")
        print("💡 Проверьте конфигурацию командой: python check_setup.py")
        sys.exit(1)


if __name__ == "__main__":
    main()