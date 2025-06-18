"""
Обработчики команд Telegram бота.
Экспорт всех роутеров для регистрации в диспетчере.
"""

from .basic import basic_router
from .analysis import analysis_router
from .visualization import visualization_router

# Список всех роутеров для регистрации в main.py
routers = [
    basic_router,
    analysis_router,
    visualization_router
]

__all__ = [
    "routers",
    "basic_router", 
    "analysis_router",
    "visualization_router"
]