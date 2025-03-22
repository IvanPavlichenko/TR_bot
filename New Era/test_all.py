"""
test_all.py

Файл для тестирования модулей:
  - strategies.py
  - risk_manager.py
  - trade_logger.py

Мы будем использовать искусственно созданные данные (dummy data) для проверки работы функций.
"""

import pandas as pd
from strategies import calculate_signal
from risk_manager import (
    calculate_position_size,
    calculate_stop_loss,
    calculate_take_profit,
)
from trade_logger import TradeLogger

# --- Тестирование стратегии (strategies.py) ---

# Создаем тестовый DataFrame для короткого таймфрейма (например, 5-минутные свечи)
data_short = {
    "open": [100, 102, 101, 103, 104],
    "high": [102, 103, 104, 105, 106],
    "low": [99, 101, 100, 102, 103],
    "close": [101, 102, 103, 104, 105],
    "volume": [1000, 1100, 1050, 1200, 1300],
}
df_short = pd.DataFrame(data_short)
df_short.index = pd.date_range(start="2025-03-15 00:00", periods=5, freq="5T")

# Создаем тестовый DataFrame для длинного таймфрейма (например, 4-часовые свечи)
data_long = {
    "open": [98, 99, 100, 101, 102],
    "high": [103, 104, 105, 106, 107],
    "low": [95, 96, 97, 98, 99],
    "close": [102, 103, 104, 105, 106],
    "volume": [2000, 2100, 2050, 2200, 2300],
}
df_long = pd.DataFrame(data_long)
df_long.index = pd.date_range(start="2025-03-15 00:00", periods=5, freq="4H")

# Рассчитываем сигнал
signal = calculate_signal(df_short, df_long)
print("Calculated signal:", signal)


# --- Тестирование риск-менеджмента (risk_manager.py) ---

# Исходные данные для теста риск-менеджмента
balance = 1000.0             # баланс в USDT
risk_per_trade = 0.05        # риск 5% от баланса
entry_price = 100.0          # цена входа
risk_distance_percent = 0.5  # стоп-лосс на 0.5% от цены входа

# Расчет стоп-лосса для лонга
stop_loss_price = calculate_stop_loss(entry_price, "long", risk_distance_percent)
# Расчет размера позиции
position_size = calculate_position_size(balance, risk_per_trade, entry_price, stop_loss_price)
# Расчет тейк-профита с соотношением риск/прибыль 2:1
take_profit_price = calculate_take_profit(entry_price, "long", risk_reward_ratio=2.0, risk_distance_percent=risk_distance_percent)

print("\nRisk Manager Test Results:")
print("Stop loss price:", stop_loss_price)
print("Position size:", position_size)
print("Take profit price:", take_profit_price)


# --- Тестирование логирования сделок (trade_logger.py) ---

# Создаем логгер сделок, который запишет данные в файл test_trades.csv
logger = TradeLogger("test_trades.csv")
logger.log_trade("buy", 0.1, 100.0, "test_order", "Test trade logging")
print("\nTest trade logged in file 'test_trades.csv'")
