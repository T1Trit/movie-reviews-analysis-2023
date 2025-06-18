"""
Проверка готовности Telegram бота к запуску.
Скрипт для валидации конфигурации и зависимостей.
"""

import sys
import importlib
from pathlib import Path
import subprocess

def check_python_version():
    """Проверка версии Python."""
    print("🐍 Проверка версии Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Проверка установленных зависимостей."""
    print("\n📦 Проверка зависимостей...")
    
    required_packages = [
        "aiogram",
        "aiohttp", 
        "pandas",
        "numpy",
        "matplotlib",
        "nltk",
        "vaderSentiment",
        "beautifulsoup4",
        "requests",
        "loguru",
        "python_dotenv",
        "pydantic",
        "sqlalchemy",
        "aiosqlite"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - не установлен")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Отсутствующие пакеты: {', '.join(missing_packages)}")
        print("💡 Установите их командой:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_environment_file():
    """Проверка .env файла."""
    print("\n🔧 Проверка переменных окружения...")
    
    env_file = Path(".env")
    env_example = Path("../.env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("❌ .env файл не найден")
            print("💡 Скопируйте .env.example и заполните:")
            print("   cp ../.env.example .env")
            return False
        else:
            print("❌ Ни .env, ни .env.example не найдены")
            return False
    
    print("✅ .env файл найден")
    return True

def check_bot_token():
    """Проверка токена бота."""
    print("\n🤖 Проверка токена бота...")
    
    try:
        from config import get_config
        config = get_config()
        
        if not config.token:
            print("❌ BOT_TOKEN не установлен")
            print("💡 Добавьте токен в .env файл:")
            print("   BOT_TOKEN=ваш_токен_от_BotFather")
            return False
        
        if len(config.token) < 10:
            print("❌ BOT_TOKEN слишком короткий")
            return False
            
        if ":" not in config.token:
            print("❌ BOT_TOKEN имеет неверный формат")
            print("💡 Правильный формат: 1234567890:ABCdefGhIjKlMnOpQrStUvWxYz")
            return False
        
        print("✅ Токен бота корректен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке токена: {e}")
        return False

def check_data_directories():
    """Проверка структуры директорий."""
    print("\n📁 Проверка директорий...")
    
    try:
        from config import init_directories, get_config
        
        config = get_config()
        init_directories()
        
        # Проверка основных директорий проекта
        main_dirs = [
            config.project_root / "data",
            config.project_root / "notebooks", 
            config.project_root / "app"
        ]
        
        for directory in main_dirs:
            if directory.exists():
                print(f"✅ {directory}")
            else:
                print(f"⚠️  {directory} - не найдена")
        
        # Проверка интеграции с данными
        if config.use_existing_data:
            if config.existing_data_file.exists():
                print(f"✅ Данные найдены: {config.existing_data_file}")
            else:
                print(f"⚠️  Данные не найдены: {config.existing_data_file}")
                print("💡 Запустите сначала основной анализ или отключите USE_EXISTING_DATA")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании директорий: {e}")
        return False

def check_nltk_data():
    """Проверка данных NLTK."""
    print("\n📚 Проверка данных NLTK...")
    
    try:
        import nltk
        
        # Проверяем наличие данных VADER
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            analyzer = SentimentIntensityAnalyzer()
            test_score = analyzer.polarity_scores("Отличный фильм!")
            print("✅ VADER Sentiment работает")
        except Exception:
            print("❌ VADER Sentiment не работает")
            print("💡 Переустановите: pip install vaderSentiment")
            return False
        
        return True
        
    except ImportError:
        print("❌ NLTK не установлен")
        return False

def check_matplotlib_backend():
    """Проверка backend для matplotlib."""
    print("\n📊 Проверка matplotlib...")
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Используем non-interactive backend
        
        import matplotlib.pyplot as plt
        
        # Тестовый график
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot([1, 2, 3], [1, 4, 2])
        ax.set_title("Test Chart")
        
        # Сохранение в память
        from io import BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        print("✅ matplotlib работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Проблема с matplotlib: {e}")
        return False

def test_basic_functionality():
    """Тест базовой функциональности."""
    print("\n🧪 Тест базовой функциональности...")
    
    try:
        # Тест конфигурации
        from config import get_config, validate_config
        config = get_config()
        validate_config()
        
        # Тест анализа настроений
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        
        test_texts = [
            "Отличный фильм, очень понравился!",
            "Ужасный фильм, не советую",
            "Нормальный фильм, можно посмотреть"
        ]
        
        for text in test_texts:
            score = analyzer.polarity_scores(text)
            print(f"   Текст: {text[:30]}...")
            print(f"   Настроение: {score['compound']:.3f}")
        
        print("✅ Основная функциональность работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в базовой функциональности: {e}")
        return False

def main():
    """Основная функция проверки."""
    print("🔍 Проверка готовности Telegram Bot")
    print("=" * 50)
    
    checks = [
        ("Python версия", check_python_version),
        ("Зависимости", check_dependencies),
        ("Файл окружения", check_environment_file),
        ("Токен бота", check_bot_token),
        ("Директории", check_data_directories),
        ("NLTK данные", check_nltk_data),
        ("matplotlib", check_matplotlib_backend),
        ("Функциональность", test_basic_functionality)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"❌ Неожиданная ошибка в {name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты: {passed}/{total} проверок пройдено")
    
    if passed == total:
        print("🎉 Все проверки пройдены! Бот готов к запуску.")
        print("💡 Запустите бота командой: python main.py")
        return True
    else:
        print("⚠️  Есть проблемы, которые нужно исправить.")
        print("💡 Устраните ошибки и запустите проверку снова.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)