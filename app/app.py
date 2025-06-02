import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from PIL import Image

# Устанавливаем ширину страницы
st.set_page_config(page_title="Анализ отзывов 2023", layout="wide")

# Заголовок дашборда
st.title("Анализ отзывов фильмов 2023 года (Кинопоиск)")
st.markdown("**Авторы:** Мекеда Богдан (ID: 466695), Меркушев Алексей (ID: 475164)")

# Загрузка обработанных данных
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/reviews_2023_final.csv", parse_dates=["review_date"])
    return df

try:
    df = load_data()
    
    # Sidebar для фильтрации
    st.sidebar.header("Фильтры")
    # Фильтр по месяцу
    months = df["review_date"].dt.to_period("M").unique().astype(str)
    selected_months = st.sidebar.multiselect("Выберите месяц(ы)", options=months, default=months)
    
    # Фильтр по оценкам
    min_rating, max_rating = st.sidebar.slider("Диапазон оценок", 0.0, 10.0, (0.0, 10.0), step=0.5)
    
    # Применяем фильтры
    df["year_month"] = df["review_date"].dt.to_period("M").astype(str)
    df_filtered = df[
        (df["year_month"].isin(selected_months)) &
        (df["rating"].between(min_rating, max_rating))
    ]
    
    st.markdown(f"**Всего отзывов после фильтрации:** {len(df_filtered)}")
    
    # --- Раздел 1: Распределение оценок ---
    st.header("Распределение оценок")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ratings = df_filtered["rating"].dropna()
    ax1.hist(ratings, bins=20, edgecolor="black")
    ax1.set_xlabel("Оценка")
    ax1.set_ylabel("Количество отзывов")
    ax1.set_title("Гистограмма распределения оценок")
    ax1.grid(axis="y", linestyle="--", alpha=0.7)
    st.pyplot(fig1)
    
    # --- Раздел 2: Временной ряд количества отзывов ---
    st.header("Временной ряд: количество отзывов по месяцам")
    reviews_per_month = df_filtered.groupby(df_filtered["review_date"].dt.to_period("M")).size().reset_index(name="count")
    reviews_per_month["review_date"] = reviews_per_month["review_date"].dt.to_timestamp()
    
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(reviews_per_month["review_date"], reviews_per_month["count"], marker="o")
    ax2.set_xlabel("Месяц")
    ax2.set_ylabel("Количество отзывов")
    ax2.set_title("Число отзывов по месяцам")
    ax2.grid(True, linestyle="--", alpha=0.7)
    st.pyplot(fig2)
    
    # --- Раздел 3: Корреляция rating vs sentiment_score ---
    st.header("Корреляция оценки и sentiment_score")
    df_corr = df_filtered.dropna(subset=["rating", "sentiment_score"])
    if len(df_corr) > 0:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.scatter(df_corr["sentiment_score"], df_corr["rating"], alpha=0.3)
        ax3.set_xlabel("Sentiment Score")
        ax3.set_ylabel("Оценка")
        ax3.set_title("Rating ↔ Sentiment Score")
        ax3.grid(True, linestyle="--", alpha=0.7)
        st.pyplot(fig3)
        
        corr_val = df_corr["rating"].corr(df_corr["sentiment_score"])
        st.markdown(f"**Коэффициент корреляции (Пирсона):** {corr_val:.3f}")
    else:
        st.write("Недостаточно данных для корреляционного анализа после фильтрации.")
    
    # --- Раздел 4: Облако слов ---
    st.header("Облако слов всех отзывов")
    try:
        wc_image = Image.open("data/processed/wordcloud_all_reviews.png")
        st.image(wc_image, caption="Word Cloud отзывов 2023", use_column_width=True)
    except FileNotFoundError:
        st.write("Файл с облаком слов не найден. Запустите сначала Jupyter Notebook для генерации визуализаций.")
    
    # --- Раздел 5: Таблица с примерными отзывами ---
    st.header("Пример отзывов после фильтрации")
    if len(df_filtered) > 0:
        st.dataframe(df_filtered[["movie_id", "review_date", "rating", "sentiment_score", "review_text"]].head(10))
    else:
        st.write("Нет отзывов, соответствующих выбранным фильтрам.")
    
    # Инструкция
    st.sidebar.markdown("""
    ---
    **Инструкция по использованию:**  
    1. В боковой панели выберите диапазон месяцев и оценок.  
    2. Дашборд автоматически обновит:  
       - Гистограмму распределения оценок.  
       - Временной ряд количества отзывов.  
       - Диаграмму корреляции rating ↔ sentiment_score.  
       - Облако слов (предварительно сохранено).  
    3. Просмотрите примеры отзывов и оцените, как меняются метрики при фильтрации.
    """)

except FileNotFoundError:
    st.error("""
    **Файл с данными не найден!**
    
    Перед запуском дашборда необходимо:
    1. Запустить Jupyter Notebook `notebooks/analysis.ipynb`
    2. Выполнить все ячейки для генерации файлов данных
    3. Убедиться, что созданы файлы в папке `data/processed/`
    
    После этого перезапустите дашборд командой:
    ```
    streamlit run app/app.py
    ```
    """)
except Exception as e:
    st.error(f"Произошла ошибка при загрузке данных: {str(e)}")
    st.write("""
    Убедитесь, что:
    1. Выполнен анализ в Jupyter Notebook
    2. Созданы все необходимые файлы данных
    3. Структура проекта соответствует ожидаемой
    """)