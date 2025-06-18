"""
Сервис создания визуализаций для Telegram бота.
Генерация графиков, диаграмм и облаков слов.
"""

import matplotlib
matplotlib.use('Agg')  # Используем non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, BytesIO
from io import BytesIO
import logging
from loguru import logger
from collections import Counter
import re

# Для облаков слов
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
    logger.warning("wordcloud не установлен, облака слов недоступны")

# Для интеграции с проектом
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class VisualizationService:
    """Сервис создания визуализаций."""
    
    def __init__(self, config=None):
        """Инициализация сервиса."""
        self.config = config
        self.logger = logger.bind(service="visualization")
        
        # Настройка matplotlib
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 100
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 11
        
        # Русские шрифты
        try:
            plt.rcParams['font.family'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']
        except:
            self.logger.warning("Проблемы с настройкой шрифтов")
        
        # Цветовая палитра
        self.colors = {
            'positive': '#2E8B57',    # Зеленый
            'negative': '#DC143C',    # Красный  
            'neutral': '#4682B4',     # Синий
            'primary': '#1f77b4',     # Основной синий
            'secondary': '#ff7f0e',   # Оранжевый
            'accent': '#2ca02c'       # Зеленый акцент
        }
    
    def create_sentiment_pie_chart(self, sentiment_data: Dict[str, int], movie_title: str) -> BytesIO:
        """Создание круговой диаграммы распределения настроений."""
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Данные для диаграммы
            labels = list(sentiment_data.keys())
            sizes = list(sentiment_data.values())
            colors = [self.colors['positive'], self.colors['negative'], self.colors['neutral']]
            
            # Создание диаграммы
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 12}
            )
            
            # Улучшение внешнего вида
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(f'Распределение настроений\\n{movie_title}', 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Легенда
            ax.legend(wedges, labels, title="Настроения", loc="center left", 
                     bbox_to_anchor=(1, 0, 0.5, 1))
            
            plt.tight_layout()
            
            # Сохранение в BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            self.logger.info(f"Создана круговая диаграмма для {movie_title}")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Ошибка создания круговой диаграммы: {e}")
            plt.close()
            raise
    
    def create_sentiment_bar_chart(self, sentiment_scores: List[float], movie_title: str) -> BytesIO:
        """Создание столбчатой диаграммы распределения оценок настроений."""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Создание бинов для группировки оценок
            bins = np.linspace(-1, 1, 21)  # 20 интервалов от -1 до 1
            hist, bin_edges = np.histogram(sentiment_scores, bins=bins)
            
            # Цвета для столбцов в зависимости от настроения
            colors = []
            for i, edge in enumerate(bin_edges[:-1]):
                mid_point = (bin_edges[i] + bin_edges[i+1]) / 2
                if mid_point >= 0.05:
                    colors.append(self.colors['positive'])
                elif mid_point <= -0.05:
                    colors.append(self.colors['negative'])
                else:
                    colors.append(self.colors['neutral'])
            
            # Создание столбчатой диаграммы
            bars = ax.bar(bin_edges[:-1], hist, width=0.08, colors=colors, 
                         edgecolor='black', linewidth=0.5, alpha=0.8)
            
            # Настройка осей
            ax.set_xlabel('Оценка настроения (compound score)', fontsize=12)
            ax.set_ylabel('Количество отзывов', fontsize=12)
            ax.set_title(f'Распределение оценок настроений\\n{movie_title}', 
                        fontsize=14, fontweight='bold', pad=15)
            
            # Добавление вертикальных линий для разделения зон
            ax.axvline(x=-0.05, color='red', linestyle='--', alpha=0.7, label='Граница негативного')
            ax.axvline(x=0.05, color='green', linestyle='--', alpha=0.7, label='Граница позитивного')
            
            # Легенда
            positive_patch = mpatches.Patch(color=self.colors['positive'], label='Позитивные')
            negative_patch = mpatches.Patch(color=self.colors['negative'], label='Негативные')
            neutral_patch = mpatches.Patch(color=self.colors['neutral'], label='Нейтральные')
            ax.legend(handles=[positive_patch, negative_patch, neutral_patch], 
                     loc='upper right')
            
            # Сетка
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Сохранение в BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            self.logger.info(f"Создана столбчатая диаграмма для {movie_title}")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Ошибка создания столбчатой диаграммы: {e}")
            plt.close()
            raise
    
    def create_rating_distribution(self, ratings: List[float], movie_title: str) -> BytesIO:
        """Создание диаграммы распределения рейтингов."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Подсчет распределения рейтингов
            unique_ratings, counts = np.unique(ratings, return_counts=True)
            
            # Цвета в зависимости от рейтинга
            colors = []
            for rating in unique_ratings:
                if rating >= 8:
                    colors.append(self.colors['positive'])
                elif rating >= 6:
                    colors.append('#FFD700')  # Золотой для средних оценок
                elif rating >= 4:
                    colors.append('#FFA500')  # Оранжевый
                else:
                    colors.append(self.colors['negative'])
            
            # Создание столбчатой диаграммы
            bars = ax.bar(unique_ratings, counts, color=colors, 
                         edgecolor='black', linewidth=0.5, alpha=0.8)
            
            # Добавление значений на столбцы
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom', fontweight='bold')
            
            # Настройка осей
            ax.set_xlabel('Рейтинг', fontsize=12)
            ax.set_ylabel('Количество отзывов', fontsize=12)
            ax.set_title(f'Распределение рейтингов\\n{movie_title}', 
                        fontsize=14, fontweight='bold', pad=15)
            
            # Настройка шкалы X
            ax.set_xticks(unique_ratings)
            ax.set_xlim(min(unique_ratings) - 0.5, max(unique_ratings) + 0.5)
            
            # Сетка
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            # Сохранение в BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            self.logger.info(f"Создана диаграмма рейтингов для {movie_title}")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Ошибка создания диаграммы рейтингов: {e}")
            plt.close()
            raise
    
    def create_wordcloud(self, texts: List[str], movie_title: str) -> Optional[BytesIO]:
        """Создание облака слов из отзывов."""
        if not WORDCLOUD_AVAILABLE:
            self.logger.error("WordCloud не установлен")
            return None
        
        try:
            # Объединение всех текстов
            all_text = ' '.join(texts)
            
            # Очистка текста
            cleaned_text = self._clean_text_for_wordcloud(all_text)
            
            if len(cleaned_text.strip()) < 10:
                self.logger.warning("Недостаточно текста для создания облака слов")
                return None
            
            # Создание облака слов
            wordcloud = WordCloud(
                width=1200, 
                height=800,
                background_color='white',
                max_words=100,
                relative_scaling=0.5,
                colormap='viridis',
                font_path=None,  # Используем системный шрифт
                margin=10
            ).generate(cleaned_text)
            
            # Создание фигуры
            fig, ax = plt.subplots(figsize=(15, 10))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(f'Облако слов отзывов\\n{movie_title}', 
                        fontsize=18, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Сохранение в BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            self.logger.info(f"Создано облако слов для {movie_title}")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Ошибка создания облака слов: {e}")
            plt.close()
            return None
    
    def _clean_text_for_wordcloud(self, text: str) -> str:
        """Очистка текста для облака слов."""
        # Удаление специальных символов
        text = re.sub(r'[^а-яёА-ЯЁa-zA-Z\\s]', ' ', text)
        
        # Удаление коротких слов
        words = text.split()
        filtered_words = [word for word in words if len(word) > 3]
        
        # Список стоп-слов
        stop_words = {
            'это', 'что', 'все', 'еще', 'уже', 'для', 'как', 'так', 
            'или', 'его', 'мне', 'мой', 'они', 'она', 'оно', 'мои',
            'был', 'была', 'было', 'были', 'есть', 'под', 'над',
            'фильм', 'кино', 'смотреть', 'посмотрел', 'видел'
        }
        
        # Удаление стоп-слов
        filtered_words = [word for word in filtered_words 
                         if word.lower() not in stop_words]
        
        return ' '.join(filtered_words)
    
    def create_summary_dashboard(self, movie_data: dict, movie_title: str) -> BytesIO:
        """Создание сводного дашборда с множественными графиками."""
        try:
            fig = plt.figure(figsize=(16, 12))
            
            # Создание сетки для размещения графиков
            gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.8], 
                                 width_ratios=[1, 1], hspace=0.3, wspace=0.3)
            
            # 1. Круговая диаграмма настроений
            ax1 = fig.add_subplot(gs[0, 0])
            sentiment_data = movie_data.get('sentiment_distribution', {})
            if sentiment_data:
                labels = list(sentiment_data.keys())
                sizes = list(sentiment_data.values())
                colors = [self.colors['positive'], self.colors['negative'], self.colors['neutral']]
                
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                       startangle=90, textprops={'fontsize': 10})
                ax1.set_title('Распределение настроений', fontsize=12, fontweight='bold')
            
            # 2. Гистограмма рейтингов
            ax2 = fig.add_subplot(gs[0, 1])
            ratings = movie_data.get('ratings', [])
            if ratings:
                unique_ratings, counts = np.unique(ratings, return_counts=True)
                colors_ratings = [self.colors['positive'] if r >= 7 else 
                                self.colors['neutral'] if r >= 5 else 
                                self.colors['negative'] for r in unique_ratings]
                
                ax2.bar(unique_ratings, counts, color=colors_ratings, alpha=0.7)
                ax2.set_title('Распределение рейтингов', fontsize=12, fontweight='bold')
                ax2.set_xlabel('Рейтинг')
                ax2.set_ylabel('Количество')
            
            # 3. Временной ряд настроений (если есть даты)
            ax3 = fig.add_subplot(gs[1, :])
            sentiment_scores = movie_data.get('sentiment_scores', [])
            if sentiment_scores:
                ax3.plot(sentiment_scores, color=self.colors['primary'], linewidth=2)
                ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                ax3.axhline(y=0.05, color='green', linestyle='--', alpha=0.5, label='Позитивная граница')
                ax3.axhline(y=-0.05, color='red', linestyle='--', alpha=0.5, label='Негативная граница')
                ax3.set_title('Динамика настроений по отзывам', fontsize=12, fontweight='bold')
                ax3.set_xlabel('Номер отзыва')
                ax3.set_ylabel('Оценка настроения')
                ax3.grid(True, alpha=0.3)
                ax3.legend()
            
            # 4. Статистическая информация
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('off')
            
            stats_text = f\"\"\"
            📊 СТАТИСТИКА АНАЛИЗА
            
            🎬 Фильм: {movie_title}
            📝 Всего отзывов: {movie_data.get('total_reviews', 'Н/Д')}
            ⭐ Средний рейтинг: {movie_data.get('avg_rating', 0):.1f}/10
            📈 Средняя оценка настроения: {movie_data.get('avg_sentiment', 0):.3f}
            
            😊 Позитивные отзывы: {movie_data.get('sentiment_distribution', {}).get('Позитивные', 0)}
            😞 Негативные отзывы: {movie_data.get('sentiment_distribution', {}).get('Негативные', 0)}
            😐 Нейтральные отзывы: {movie_data.get('sentiment_distribution', {}).get('Нейтральные', 0)}
            \"\"\"
            
            ax4.text(0.5, 0.5, stats_text, transform=ax4.transAxes, 
                    fontsize=11, verticalalignment='center', 
                    horizontalalignment='center',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.5))
            
            # Общий заголовок
            fig.suptitle(f'Сводный анализ отзывов: {movie_title}', 
                        fontsize=16, fontweight='bold', y=0.95)
            
            # Сохранение в BytesIO
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close()
            
            self.logger.info(f"Создан сводный дашборд для {movie_title}")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Ошибка создания сводного дашборда: {e}")
            plt.close()
            raise

# Глобальный экземпляр сервиса
_visualization_service: Optional[VisualizationService] = None

def get_visualization_service(config=None) -> VisualizationService:
    """Получение экземпляра сервиса (синглтон)."""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService(config)
    return _visualization_service

if __name__ == "__main__":
    """Тестирование сервиса."""
    service = VisualizationService()
    
    # Тестовые данные
    sentiment_data = {"Позитивные": 30, "Негативные": 10, "Нейтральные": 15}
    sentiment_scores = np.random.normal(0.1, 0.3, 100).tolist()
    ratings = np.random.choice(range(1, 11), 50).tolist()
    
    print("🧪 Тестирование создания графиков...")
    
    try:
        # Тест круговой диаграммы
        buffer = service.create_sentiment_pie_chart(sentiment_data, "Тестовый фильм")
        print("✅ Круговая диаграмма создана")
        
        # Тест столбчатой диаграммы
        buffer = service.create_sentiment_bar_chart(sentiment_scores, "Тестовый фильм")
        print("✅ Столбчатая диаграмма создана")
        
        # Тест диаграммы рейтингов
        buffer = service.create_rating_distribution(ratings, "Тестовый фильм")
        print("✅ Диаграмма рейтингов создана")
        
        print("🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")