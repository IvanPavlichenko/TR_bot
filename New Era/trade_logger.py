"""
trade_logger.py

Модуль для логирования совершённых сделок.
Записывает данные о сделках в CSV-файл для последующего анализа.
"""

import csv
from datetime import datetime


class TradeLogger:
    def __init__(self, filename: str = "trades.csv"):
        self.filename = filename
        self.initialize_file()

    def initialize_file(self):
        """
        Если файл не существует, создаём его и записываем заголовок.
        """
        try:
            with open(self.filename, "x", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "side", "amount", "price", "order_id", "note"])
        except FileExistsError:
            # Файл уже существует – ничего не делаем
            pass

    def log_trade(self, side: str, amount: float, price: float, order_id: str = "", note: str = ""):
        """
        Логирует сделку в CSV-файл.

        Параметры:
          side      - направление сделки ('buy' или 'sell')
          amount    - количество актива
          price     - цена сделки
          order_id  - идентификатор ордера (если есть)
          note      - дополнительные примечания (например, причина входа/выхода)
        """
        with open(self.filename, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.now().isoformat(), side, amount, price, order_id, note])


# Пример использования модуля
if __name__ == "__main__":
    logger = TradeLogger()
    # Пример логирования сделки: покупка 0.01 единиц актива по цене 50000, идентификатор ордера "order123"
    logger.log_trade("buy", 0.01, 50000, "order123", "тестовая сделка")
    print("Сделка залогирована в файле trades.csv")
