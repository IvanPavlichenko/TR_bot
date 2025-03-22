"""
data_fetcher.py

Модуль для получения и предварительной обработки рыночных данных через API биржи.
Использует библиотеку ccxt для получения исторических данных OHLCV и преобразует их в pandas DataFrame.
"""

import pandas as pd


class DataFetcher:
    def __init__(self, exchange, symbol):
        """
        Инициализирует DataFetcher.

        Параметры:
          exchange - объект биржи (например, созданный через ccxt)
          symbol - торговая пара, например 'BTC/USDT'
        """
        self.exchange = exchange
        self.symbol = symbol

    def fetch_ohlcv(self, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """
        Получает OHLCV-данные для указанного таймфрейма.

        Параметры:
          timeframe - таймфрейм свечей (например, '5m', '1h', '4h', '1d')
          limit - количество свечей для получения

        Возвращает:
          DataFrame с колонками: 'open', 'high', 'low', 'close', 'volume'
          и индексом с временными метками.
        """
        try:
            # Получаем данные через ccxt: [timestamp, open, high, low, close, volume]
            data = self.exchange.fetch_ohlcv(self.symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            # Приводим все числовые значения к float
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            return df
        except Exception as e:
            print(f"Ошибка при получении данных OHLCV: {e}")
            return pd.DataFrame()  # Вернуть пустой DataFrame в случае ошибки


# Пример использования модуля (для самостоятельного тестирования)
if __name__ == "__main__":
    import ccxt

    # Здесь необходимо заменить на реальные данные или использовать paper-trading
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    symbol = "BTC/USDT"
    fetcher = DataFetcher(exchange, symbol)
    df = fetcher.fetch_ohlcv("5m", limit=50)
    print(df.head())
