"""
Конфигурация для Telegram бота анализа отзывов фильмов.
Интегрированная версия для проекта movie-reviews-analysis-2023.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from dataclasses import dataclass
import sys

# Загружаем переменные из .env файла
load_dotenv()

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных."""
    url: str = "sqlite:///telegram_bot/data/bot.db"
    echo: bool = False
    
@dataclass 
class CacheConfig:
    """Конфигурация кэширования."""
    ttl: int = 3600
    max_size: int = 1000
    enabled: bool = True

@dataclass
class LoggingConfig:
    """Конфигурация логирования."""
    level: str = "INFO"
    file: str = "telegram_bot/logs/bot.log"
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    rotation: str = "1 day"
    retention: str = "7 days"

@dataclass
class KinopoiskConfig:
    """Конфигурация парсинга Кинопоиска."""
    delay: float = 2.0
    max_reviews: int = 50
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

@dataclass
class LimitsConfig:
    """Лимиты для пользователей."""
    requests_per_hour: int = 10
    requests_per_day: int = 50
    concurrent_requests: int = 5

class BotConfig:
    """Основная конфигурация бота."""
    
    def __init__(self):
        # Токен бота
        self.token = os.getenv("BOT_TOKEN", "")
        
        # Режимы работы
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.webhook_mode = os.getenv("WEBHOOK_MODE", "false").lower() == "true"
        self.webhook_url = os.getenv("WEBHOOK_URL", "")
        self.webhook_port = int(os.getenv("WEBHOOK_PORT", "8443"))
        self.webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
        
        # Пути к директориям
        self.base_path = Path(__file__).parent
        self.project_root = self.base_path.parent  # Корень основного проекта
        
        # Директории бота
        self.data_path = self.base_path / "data"
        self.charts_path = self.data_path / "charts" 
        self.wordclouds_path = self.data_path / "wordclouds"
        self.cache_path = self.data_path / "cache"
        self.logs_path = self.base_path / "logs"
        self.temp_path = self.data_path / "temp"
        
        # Интеграция с основным проектом
        self.main_data_path = self.project_root / "data"
        self.processed_data_path = self.main_data_path / "processed"
        self.existing_data_file = self.processed_data_path / "reviews_2023_final.csv"
        
        # Использование существующих данных
        self.use_existing_data = os.getenv("USE_EXISTING_DATA", "true").lower() == "true"
        
        # Компоненты конфигурации
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///telegram_bot/data/bot.db"),
            echo=self.debug
        )
        
        self.cache = CacheConfig(
            ttl=int(os.getenv("CACHE_TTL", "3600")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            enabled=os.getenv("ENABLE_CACHE", "true").lower() == "true"
        )
        
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE", "telegram_bot/logs/bot.log")
        )
        
        self.kinopoisk = KinopoiskConfig(
            delay=float(os.getenv("KINOPOISK_DELAY", "2.0")),
            max_reviews=int(os.getenv("MAX_REVIEWS_PER_MOVIE", "50")),
            timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
        )
        
        self.limits = LimitsConfig(
            requests_per_hour=int(os.getenv("MAX_REQUESTS_PER_HOUR", "10")),
            requests_per_day=int(os.getenv("MAX_REQUESTS_PER_DAY", "50")),
            concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        )
        
        # Визуализация
        self.figure_dpi = int(os.getenv("FIGURE_DPI", "100"))
        self.figure_size = (
            int(os.getenv("FIGURE_SIZE_WIDTH", "12")),
            int(os.getenv("FIGURE_SIZE_HEIGHT", "8"))
        )
        
        # Безопасность
        self.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
        self.allowed_users = self._parse_user_list(os.getenv("ALLOWED_USERS", ""))
        self.admin_users = self._parse_user_list(os.getenv("ADMIN_USERS", ""))
        
        # Сторонние сервисы
        self.sentry_dsn = os.getenv("SENTRY_DSN", "")
        
    def _parse_user_list(self, users_str: str) -> list[int]:
        """Парсинг списка пользователей."""
        if not users_str:
            return []
        return [int(user_id.strip()) for user_id in users_str.split(",") if user_id.strip()]

# Глобальный экземпляр конфигурации
_config: Optional[BotConfig] = None

def get_config() -> BotConfig:
    """Получить конфигурацию (синглтон)."""
    global _config
    if _config is None:
        _config = BotConfig()
    return _config

def init_directories():
    """Создание необходимых директорий."""
    config = get_config()
    
    directories = [
        config.data_path,
        config.charts_path,
        config.wordclouds_path,
        config.cache_path,
        config.logs_path,
        config.temp_path
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        
    print(f"✅ Директории созданы: {len(directories)} папок")

def validate_config():
    """Валидация конфигурации."""
    config = get_config()
    errors = []
    
    # Проверка токена
    if not config.token:
        errors.append("❌ BOT_TOKEN не установлен в .env файле")
    elif len(config.token) < 10:
        errors.append("❌ BOT_TOKEN слишком короткий")
    elif not config.token.startswith(("1", "2", "5", "6")):
        errors.append("❌ BOT_TOKEN имеет неверный формат")
    
    # Проверка webhook режима
    if config.webhook_mode and not config.webhook_url:
        errors.append("❌ WEBHOOK_URL не установлен для webhook режима")
    
    # Проверка интеграции с основным проектом
    if config.use_existing_data and not config.existing_data_file.exists():
        errors.append(f"❌ Файл данных не найден: {config.existing_data_file}")
    
    # Проверка директорий
    if not config.project_root.exists():
        errors.append(f"❌ Корневая директория проекта не найдена: {config.project_root}")
    
    # Проверка прав записи
    try:
        test_file = config.data_path / "test_write.tmp"
        config.data_path.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        errors.append(f"❌ Нет прав на запись в директорию данных: {e}")
    
    if errors:
        print("\n".join(errors))
        raise ValueError(f"Ошибки конфигурации: {len(errors)} проблем")
    
    print("✅ Конфигурация валидна")

def print_config_summary():
    """Вывод сводки конфигурации."""
    config = get_config()
    
    print("🤖 Конфигурация Telegram Bot")
    print("=" * 50)
    print(f"Режим работы: {'Webhook' if config.webhook_mode else 'Long Polling'}")
    print(f"Debug режим: {'Включен' if config.debug else 'Выключен'}")
    print(f"Использовать существующие данные: {'Да' if config.use_existing_data else 'Нет'}")
    print(f"Лимит запросов в час: {config.limits.requests_per_hour}")
    print(f"Максимум отзывов на фильм: {config.kinopoisk.max_reviews}")
    print(f"Задержка между запросами: {config.kinopoisk.delay}с")
    print(f"TTL кэша: {config.cache.ttl}с")
    print(f"Директория данных: {config.data_path}")
    if config.use_existing_data:
        print(f"Файл данных: {config.existing_data_file}")
    print("=" * 50)

if __name__ == "__main__":
    """Тестирование конфигурации."""
    try:
        print("🔧 Проверка конфигурации...")
        validate_config()
        print_config_summary()
        init_directories()
        print("✅ Конфигурация готова к работе!")
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        sys.exit(1)