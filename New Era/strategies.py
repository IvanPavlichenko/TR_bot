"""
strategies.py

Модуль с функцией для расчёта торгового сигнала на основе анализа данных с двух таймфреймов.
Используем индикаторы: EMA, RSI и простой объёмный фильтр.

Функция calculate_signal принимает два DataFrame:
  - df_short: данные для короткого таймфрейма (например, '5m')
  - df_long: данные для длинного таймфрейма (например, '4h')

Возвращает:
  - "long", если условия для покупки выполнены,
  - "short", если условия для продажи выполнены,
  - None, если сигнал не определён.
"""

import pandas as pd
import ta


def calculate_signal(df_short: pd.DataFrame, df_long: pd.DataFrame) -> str:
    # ----- Индикаторы на коротком таймфрейме ----- #
    # Расчёт экспоненциальных скользящих средних (EMA)
    df_short["ema_9"] = ta.trend.EMAIndicator(df_short["close"], window=9).ema_indicator()
    df_short["ema_20"] = ta.trend.EMAIndicator(df_short["close"], window=20).ema_indicator()

    # Расчёт RSI
    df_short["rsi"] = ta.momentum.RSIIndicator(df_short["close"], window=14).rsi()

    # Простой фильтр по объёмам: скользящее среднее объёма
    df_short["vol_ma"] = df_short["volume"].rolling(window=20).mean()

    # ----- Индикаторы на длинном таймфрейме ----- #
    df_long["ema_50"] = ta.trend.EMAIndicator(df_long["close"], window=50).ema_indicator()

    # Извлекаем последние доступные значения
    short_ema_9 = df_short["ema_9"].iloc[-1]
    short_ema_20 = df_short["ema_20"].iloc[-1]
    short_rsi = df_short["rsi"].iloc[-1]
    last_volume = df_short["volume"].iloc[-1]
    avg_volume = df_short["vol_ma"].iloc[-1]

    long_ema_50 = df_long["ema_50"].iloc[-1]
    long_close_price = df_long["close"].iloc[-1]

    # Определяем тренд на длинном таймфрейме: восходящий, если цена выше EMA_50
    is_uptrend_long = long_close_price > long_ema_50

    # Фильтр по объёму: сигнал считается, если текущий объём выше среднего
    volume_ok = last_volume > avg_volume

    signal = None

    # Условие для сигнала "long":
    # - EMA_9 > EMA_20 (бычий сигнал на коротком ТФ)
    # - RSI ниже 70 (рынок не перекуплен)
    # - На длинном ТФ установлен восходящий тренд
    # - Текущий объём выше среднего
    if short_ema_9 > short_ema_20 and short_rsi < 70 and is_uptrend_long and volume_ok:
        signal = "long"
    # Условие для сигнала "short":
    # - EMA_9 < EMA_20 (медвежий сигнал на коротком ТФ)
    # - RSI выше 30 (рынок не слишком перепродан)
    # - На длинном ТФ отсутствует восходящий тренд
    # - Текущий объём выше среднего
    elif short_ema_9 < short_ema_20 and short_rsi > 30 and not is_uptrend_long and volume_ok:
        signal = "short"

    return signal
