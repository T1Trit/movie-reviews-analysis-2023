"""
Сервис анализа настроений для Telegram бота.
Интеграция с данными основного проекта и VADER Sentiment Analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging
from loguru import logger

# Для интеграции с основным проектом
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class SentimentResult:
    """Результат анализа настроений."""
    positive: float
    negative: float
    neutral: float
    compound: float
    
    @property
    def dominant_sentiment(self) -> str:
        """Определение доминирующего настроения."""
        if self.compound >= 0.05:
            return "positive"
        elif self.compound <= -0.05:
            return "negative"
        else:
            return "neutral"
    
    @property
    def sentiment_emoji(self) -> str:
        """Эмодзи для настроения."""
        if self.dominant_sentiment == "positive":
            return "😊"
        elif self.dominant_sentiment == "negative":
            return "😞"
        else:
            return "😐"

@dataclass
class MovieAnalysis:
    """Результат анализа фильма."""
    movie_id: int
    movie_title: str
    total_reviews: int
    avg_rating: float
    sentiment_stats: Dict[str, float]
    reviews_sample: List[str]
    sentiment_scores: List[float]

class SentimentService:
    """Сервис анализа настроений отзывов."""
    
    def __init__(self, config=None):
        """Инициализация сервиса."""
        self.config = config
        self.analyzer = SentimentIntensityAnalyzer()
        self._existing_data: Optional[pd.DataFrame] = None
        
        # Настройка логирования
        self.logger = logger.bind(service="sentiment")
        
    def load_existing_data(self) -> bool:
        """Загрузка существующих данных проекта."""
        try:
            if self.config and self.config.use_existing_data:
                data_file = self.config.existing_data_file
                if data_file.exists():
                    self._existing_data = pd.read_csv(data_file)
                    self.logger.info(f"Загружены данные: {len(self._existing_data)} отзывов")
                    return True
            
            # Альтернативные пути поиска данных
            possible_paths = [
                Path("../data/processed/reviews_2023_final.csv"),
                Path("data/processed/reviews_2023_final.csv"),
                Path("../data/processed/reviews_2023_cleaned.csv"),
                Path("data/processed/reviews_2023_cleaned.csv")
            ]
            
            for path in possible_paths:
                if path.exists():
                    self._existing_data = pd.read_csv(path)
                    self.logger.info(f"Найдены данные: {path} ({len(self._existing_data)} отзывов)")
                    return True
            
            self.logger.warning("Существующие данные не найдены, будет использован парсинг")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
            return False
    
    def analyze_text(self, text: str) -> SentimentResult:
        """Анализ настроения одного текста."""
        try:
            scores = self.analyzer.polarity_scores(text)
            return SentimentResult(
                positive=scores['pos'],
                negative=scores['neg'],
                neutral=scores['neu'],
                compound=scores['compound']
            )
        except Exception as e:
            self.logger.error(f"Ошибка анализа текста: {e}")
            # Возвращаем нейтральный результат при ошибке
            return SentimentResult(0.0, 0.0, 1.0, 0.0)
    
    def analyze_reviews_batch(self, reviews: List[str]) -> List[SentimentResult]:
        """Пакетный анализ отзывов."""
        results = []
        for review in reviews:
            result = self.analyze_text(review)
            results.append(result)
        return results
    
    def get_movie_sentiment_stats(self, movie_id: int) -> Optional[MovieAnalysis]:
        """Получение статистики настроений для фильма."""
        try:
            # Попытка использовать существующие данные
            if self._existing_data is not None:
                movie_data = self._existing_data[
                    self._existing_data['movie_id'] == movie_id
                ] if 'movie_id' in self._existing_data.columns else None
                
                if movie_data is not None and len(movie_data) > 0:
                    return self._analyze_existing_data(movie_data, movie_id)
            
            # Если данных нет, возвращаем None (потребуется парсинг)
            self.logger.info(f"Данные для фильма {movie_id} не найдены в существующих данных")
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа фильма {movie_id}: {e}")
            return None
    
    def _analyze_existing_data(self, movie_data: pd.DataFrame, movie_id: int) -> MovieAnalysis:
        """Анализ существующих данных фильма."""
        # Получение названия фильма
        movie_title = movie_data['movie_title'].iloc[0] if 'movie_title' in movie_data.columns else f"Фильм {movie_id}"
        
        # Получение отзывов
        review_column = self._find_review_column(movie_data)
        reviews = movie_data[review_column].dropna().tolist()
        
        # Анализ настроений
        sentiment_results = self.analyze_reviews_batch(reviews)
        
        # Подсчет статистики
        total_reviews = len(reviews)
        positive_count = sum(1 for r in sentiment_results if r.dominant_sentiment == "positive")
        negative_count = sum(1 for r in sentiment_results if r.dominant_sentiment == "negative")
        neutral_count = sum(1 for r in sentiment_results if r.dominant_sentiment == "neutral")
        
        sentiment_stats = {
            "positive_percent": (positive_count / total_reviews) * 100,
            "negative_percent": (negative_count / total_reviews) * 100,
            "neutral_percent": (neutral_count / total_reviews) * 100,
            "avg_compound": np.mean([r.compound for r in sentiment_results])
        }
        
        # Средний рейтинг
        rating_column = self._find_rating_column(movie_data)
        avg_rating = movie_data[rating_column].mean() if rating_column else 0.0
        
        # Выборка отзывов для примера
        reviews_sample = reviews[:10] if len(reviews) >= 10 else reviews
        sentiment_scores = [r.compound for r in sentiment_results]
        
        return MovieAnalysis(
            movie_id=movie_id,
            movie_title=movie_title,
            total_reviews=total_reviews,
            avg_rating=avg_rating,
            sentiment_stats=sentiment_stats,
            reviews_sample=reviews_sample,
            sentiment_scores=sentiment_scores
        )
    
    def _find_review_column(self, df: pd.DataFrame) -> str:
        """Поиск колонки с отзывами."""
        possible_columns = ['review_text', 'review', 'text', 'content', 'comment']
        for col in possible_columns:
            if col in df.columns:
                return col
        # Если не найдено, возвращаем первую текстовую колонку
        text_columns = df.select_dtypes(include=['object']).columns
        return text_columns[0] if len(text_columns) > 0 else df.columns[0]
    
    def _find_rating_column(self, df: pd.DataFrame) -> Optional[str]:
        """Поиск колонки с рейтингами."""
        possible_columns = ['rating', 'score', 'user_rating', 'grade']
        for col in possible_columns:
            if col in df.columns:
                return col
        return None
    
    def get_sentiment_distribution(self, movie_id: int) -> Optional[Dict[str, int]]:
        """Получение распределения настроений для визуализации."""
        analysis = self.get_movie_sentiment_stats(movie_id)
        if not analysis:
            return None
        
        total = analysis.total_reviews
        return {
            "Позитивные": int(analysis.sentiment_stats["positive_percent"] * total / 100),
            "Негативные": int(analysis.sentiment_stats["negative_percent"] * total / 100), 
            "Нейтральные": int(analysis.sentiment_stats["neutral_percent"] * total / 100)
        }
    
    def format_sentiment_summary(self, movie_id: int) -> Optional[str]:
        """Форматирование краткой сводки анализа."""
        analysis = self.get_movie_sentiment_stats(movie_id)
        if not analysis:
            return None
        
        summary = f"""📊 <b>Анализ настроений: {analysis.movie_title}</b>

📝 <b>Статистика:</b>
• Всего отзывов: {analysis.total_reviews}
• Средний рейтинг: {analysis.avg_rating:.1f}/10

😊 <b>Распределение настроений:</b>
• Позитивные: {analysis.sentiment_stats['positive_percent']:.1f}%
• Негативные: {analysis.sentiment_stats['negative_percent']:.1f}%
• Нейтральные: {analysis.sentiment_stats['neutral_percent']:.1f}%

📈 <b>Общая оценка:</b> {analysis.sentiment_stats['avg_compound']:.3f}
"""
        
        # Добавляем интерпретацию
        avg_compound = analysis.sentiment_stats['avg_compound']
        if avg_compound >= 0.1:
            summary += "✅ <i>Общее восприятие: положительное</i>"
        elif avg_compound <= -0.1:
            summary += "❌ <i>Общее восприятие: отрицательное</i>"
        else:
            summary += "😐 <i>Общее восприятие: нейтральное</i>"
        
        return summary

# Глобальный экземпляр сервиса
_sentiment_service: Optional[SentimentService] = None

def get_sentiment_service(config=None) -> SentimentService:
    """Получение экземпляра сервиса (синглтон)."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService(config)
        _sentiment_service.load_existing_data()
    return _sentiment_service

if __name__ == "__main__":
    """Тестирование сервиса."""
    service = SentimentService()
    
    # Тест анализа текста
    test_texts = [
        "Отличный фильм, очень понравился!",
        "Ужасный фильм, время потрачено зря",
        "Обычный фильм, ничего особенного"
    ]
    
    print("🧪 Тестирование анализа настроений:")
    for text in test_texts:
        result = service.analyze_text(text)
        print(f"Текст: {text}")
        print(f"Результат: {result.dominant_sentiment} ({result.compound:.3f})")
        print(f"Эмодзи: {result.sentiment_emoji}")
        print("---")
    
    # Тест загрузки данных
    if service.load_existing_data():
        print("✅ Существующие данные загружены успешно")
    else:
        print("⚠️ Существующие данные не найдены")