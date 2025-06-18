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
from bot.handlers import routers


async def on_startup():
    """Инициализация при запуске бота."""
    logger.info("🚀 Запуск Telegram бота анализа отзывов фильмов...")
    
    # Инициализация директорий
    init_directories()
    logger.info("📁 Директории инициализированы")
    
    # Инициализация сервисов
    try:
        from bot.services.sentiment_service import get_sentiment_service
        from bot.services.visualization_service import get_visualization_service
        
        config = get_config()
        
        # Инициализация сервиса анализа настроений
        sentiment_service = get_sentiment_service(config)
        if sentiment_service.load_existing_data():
            logger.info("📊 Сервис анализа настроений инициализирован с существующими данными")
        else:
            logger.info("📊 Сервис анализа настроений инициализирован (без предзагруженных данных)")
        
        # Инициализация сервиса визуализации
        viz_service = get_visualization_service(config)
        logger.info("📈 Сервис визуализации инициализирован")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации сервисов: {e}")
    
    logger.info("✅ Бот успешно запущен и готов к работе!")


async def on_shutdown():
    """Очистка ресурсов при остановке бота."""
    logger.info("🔄 Остановка бота...")
    
    # Очистка временных файлов
    try:
        config = get_config()
        temp_dir = config.temp_path
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
            logger.info("🧹 Временные файлы очищены")
    except Exception as e:
        logger.warning(f"Проблема при очистке временных файлов: {e}")
    
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
    
    # Регистрация всех роутеров
    for router in routers:
        dp.include_router(router)
        logger.info(f"🔗 Зарегистрирован роутер: {router.name if hasattr(router, 'name') else 'unnamed'}")
    
    logger.info(f"📋 Всего зарегистрировано роутеров: {len(routers)}")
    
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
    app.router.add_get("/status", bot_status)
    
    return app


async def health_check(request):
    """Проверка здоровья сервиса."""
    config = get_config()
    return web.json_response({
        "status": "ok", 
        "service": "movie-reviews-bot",
        "version": "1.0",
        "integration": "movie-reviews-analysis-2023",
        "data_integration": config.use_existing_data,
        "timestamp": str(asyncio.get_event_loop().time())
    })


async def bot_status(request):
    """Подробный статус бота."""
    config = get_config()
    
    # Проверка сервисов
    services_status = {}
    try:
        from bot.services.sentiment_service import get_sentiment_service
        sentiment_service = get_sentiment_service(config)
        services_status["sentiment"] = "ok" if sentiment_service else "error"
    except Exception:
        services_status["sentiment"] = "error"
    
    try:
        from bot.services.visualization_service import get_visualization_service
        viz_service = get_visualization_service(config)
        services_status["visualization"] = "ok" if viz_service else "error"
    except Exception:
        services_status["visualization"] = "error"
    
    return web.json_response({
        "bot": {
            "version": "1.0",
            "mode": "webhook" if config.webhook_mode else "polling",
            "debug": config.debug
        },
        "integration": {
            "project_root": str(config.project_root),
            "use_existing_data": config.use_existing_data,
            "data_file_exists": config.existing_data_file.exists() if config.use_existing_data else None
        },
        "services": services_status,
        "limits": {
            "requests_per_hour": config.limits.requests_per_hour,
            "max_reviews": config.kinopoisk.max_reviews
        },
        "handlers": len(routers),
        "timestamp": str(asyncio.get_event_loop().time())
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
        logger.info("🎬 Запуск Telegram бота анализа отзывов фильмов")
        logger.info(f"📂 Проект: {config.project_root}")
        logger.info(f"🔧 Режим: {'Webhook' if config.webhook_mode else 'Long Polling'}")
        logger.info(f"📊 Интеграция с данными: {'Включена' if config.use_existing_data else 'Отключена'}")
        logger.info(f"📋 Количество обработчиков: {len(routers)}")
        
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