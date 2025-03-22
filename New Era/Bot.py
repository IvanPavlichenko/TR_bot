"""
Bot.py

Бот для торговли на OKX бессрочными контрактами (swap) с изолированной маржей.
Расчёт размера позиции осуществляется на основе фиксированной суммы маржи (FIXED_MARGIN_AMOUNT)
с учетом плеча (для каждой пары из LEVERAGE_DICT):
    position_size = (FIXED_MARGIN_AMOUNT * leverage) / price

Уведомления в Telegram отправляются:
  - При запуске бота.
  - При получении сигнала (вход в позицию).
  - При выходе из позиции (факт фиксации профита или стоп‑лосса).

Перед запуском:
  - Проверьте параметры в config.py (включая TELEGRAM_TOKEN и TELEGRAM_CHAT_IDS).
  - Убедитесь, что trade_logger.py находится в той же директории.
  - Для реальной торговли установите IS_PAPERTRADING = False.
"""

import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime
import traceback
import ta
import requests

# Импорт параметров из config.py
from config import (
    API_KEY, API_SECRET, API_PASSPHRASE,
    EXCHANGE_ID, SYMBOLS, TF_SHORT, TF_LONG, CANDLE_LIMIT,
    LOOP_DELAY, IS_PAPERTRADING, PAPER_BALANCE_USDT,
    RISK_PER_TRADE, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT,
    ATR_WINDOW, ATR_MULTIPLIER, TRAILING_STOP_MULTIPLIER,
    MIN_ORDER_AMOUNT, FIXED_MARGIN_AMOUNT,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS,
    LEVERAGE_DICT, DEFAULT_LEVERAGE
)

# Импорт модуля логирования сделок
from trade_logger import TradeLogger

class MultiTFBot:
    def __init__(self, api_key, api_secret, api_passphrase, exchange_id, symbol):
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            "apiKey": api_key,
            "secret": api_secret,
            "password": api_passphrase,
            "enableRateLimit": True,
            "options": {"defaultType": "swap"}
        })
        self.symbol = symbol
        self.paper_balance = PAPER_BALANCE_USDT
        self.current_position = None  # "long", "short" или None
        self.entry_price = None
        self.entry_time = None
        self.logger = TradeLogger("trades.csv")

        # Уведомление при запуске
        self.send_telegram_message(f"Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for {self.symbol}.")

    def send_telegram_message(self, message):
        """Отправляет сообщение в Telegram для всех chat_id из списка TELEGRAM_CHAT_IDS."""
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        for chat_id in TELEGRAM_CHAT_IDS:
            payload = {"chat_id": chat_id, "text": message}
            try:
                r = requests.post(url, data=payload)
                if r.status_code != 200:
                    print(f"Telegram error for chat {chat_id}:", r.text)
            except Exception as e:
                print(f"Telegram exception for chat {chat_id}:", e)

    def fetch_ohlcv(self, timeframe, limit=CANDLE_LIMIT):
        data = self.exchange.fetch_ohlcv(self.symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df

    def calculate_indicators(self, df_short, df_long):
        df_short["ema_9"] = ta.trend.EMAIndicator(df_short["close"], window=9).ema_indicator()
        df_short["ema_20"] = ta.trend.EMAIndicator(df_short["close"], window=20).ema_indicator()
        df_short["rsi"] = ta.momentum.RSIIndicator(df_short["close"], window=14).rsi()
        df_short["vol_ma"] = df_short["volume"].rolling(window=20).mean()

        df_long["ema_50"] = ta.trend.EMAIndicator(df_long["close"], window=50).ema_indicator()

        ema9 = df_short["ema_9"].iloc[-1]
        ema20 = df_short["ema_20"].iloc[-1]
        rsi = df_short["rsi"].iloc[-1]
        last_volume = df_short["volume"].iloc[-1]
        vol_ma = df_short["vol_ma"].iloc[-1]

        long_ema50 = df_long["ema_50"].iloc[-1]
        long_close = df_long["close"].iloc[-1]

        is_uptrend_long = long_close > long_ema50
        volume_ok = last_volume > vol_ma

        signal = None
        if ema9 > ema20 and rsi < 70 and is_uptrend_long and volume_ok:
            signal = "long"
        elif ema9 < ema20 and rsi > 30 and not is_uptrend_long and volume_ok:
            signal = "short"

        indicator_values = {
            "EMA_9": ema9,
            "EMA_20": ema20,
            "RSI": rsi,
            "Last Volume": last_volume,
            "Volume MA": vol_ma,
            "Long EMA_50": long_ema50,
            "Long Close Price": long_close,
            "Is Uptrend Long": is_uptrend_long,
            "Volume OK": volume_ok
        }
        return signal, indicator_values

    def calculate_position_size(self, price):
        leverage = LEVERAGE_DICT.get(self.symbol, DEFAULT_LEVERAGE)
        amount_asset = (FIXED_MARGIN_AMOUNT * leverage) / price
        if amount_asset < MIN_ORDER_AMOUNT:
            print(f"Calculated order size {amount_asset:.6f} is below minimum {MIN_ORDER_AMOUNT}. Adjusting to minimum.")
            amount_asset = MIN_ORDER_AMOUNT
        print(f"Using fixed margin: {FIXED_MARGIN_AMOUNT} USDT, Leverage: {leverage}, Price: {price}, Position size: {amount_asset:.6f} {self.symbol.split('/')[0]}")
        return amount_asset

    def place_order(self, side, amount, price):
        msg = f"[ORDER] {side.upper()} {amount:.6f} {self.symbol} at price {price:.4f}"
        print(msg)
        self.send_telegram_message(msg)
        if IS_PAPERTRADING:
            self.logger.log_trade(side, amount, price, "SIMULATED", "Paper-trading simulation")
            return
        try:
            order = self.exchange.create_order(
                symbol=self.symbol,
                type="market",
                side=side,
                amount=amount,
                params={
                    "marginMode": "isolated",
                    "posSide": "long" if side.lower() == "buy" else "short"
                }
            )
            print("[EXCHANGE RESPONSE]", order)
            order_id = order.get("id", "")
            self.logger.log_trade(side, amount, price, order_id, "Live order executed")
        except Exception as e:
            error_msg = f"[ERROR PLACING ORDER] {e}"
            print(error_msg)
            self.send_telegram_message(error_msg)

    def calculate_profit_percent(self, current_price):
        if self.entry_price is None:
            return 0.0
        if self.current_position == "long":
            profit = (current_price - self.entry_price) / self.entry_price * 100
        elif self.current_position == "short":
            profit = (self.entry_price - current_price) / self.entry_price * 100
        else:
            profit = 0.0
        return profit

    def run(self):
        while True:
            try:
                now = datetime.now()
                print(f"\n[{now}] --- BOT CYCLE START ---")
                df_short = self.fetch_ohlcv(TF_SHORT, limit=CANDLE_LIMIT)
                df_long = self.fetch_ohlcv(TF_LONG, limit=CANDLE_LIMIT)
                signal, indicators = self.calculate_indicators(df_short, df_long)
                latest_price = df_short["close"].iloc[-1]

                # Логируем индикаторы (без периодических обновлений)
                indicators_str = "\n".join([f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                                             for k, v in indicators.items()])
                print("Indicator values:")
                print(indicators_str)

                # Если позиция открыта, проверяем профит и условия выхода
                if self.current_position is not None:
                    profit_pct = self.calculate_profit_percent(latest_price)
                    pos_msg = f"Position update for {self.symbol}:\nEntry Time: {self.entry_time.strftime('%Y-%m-%d %H:%M:%S')}\nEntry Price: {self.entry_price:.4f}\nCurrent Price: {latest_price:.4f}\nProfit: {profit_pct:.2f}%"
                    print(pos_msg)
                    # При достижении порогов выхода отправляем уведомление и закрываем позицию
                    if profit_pct >= TAKE_PROFIT_PERCENT:
                        exit_msg = f"Take Profit reached ({TAKE_PROFIT_PERCENT}%) for {self.symbol}. Exiting position."
                        print(exit_msg)
                        self.send_telegram_message(exit_msg)
                        if self.current_position == "long":
                            amount = self.calculate_position_size(latest_price)
                            self.place_order("sell", amount, latest_price)
                        elif self.current_position == "short":
                            amount = self.calculate_position_size(latest_price)
                            self.place_order("buy", amount, latest_price)
                        full_exit_msg = f"Exited position for {self.symbol}:\nEntry: {self.entry_time.strftime('%Y-%m-%d %H:%M:%S')} at {self.entry_price:.4f}\nExit: {now.strftime('%Y-%m-%d %H:%M:%S')} at {latest_price:.4f}\nProfit: {profit_pct:.2f}%"
                        print(full_exit_msg)
                        self.send_telegram_message(full_exit_msg)
                        self.current_position = None
                        self.entry_price = None
                        self.entry_time = None
                        time.sleep(LOOP_DELAY)
                        continue
                    elif profit_pct <= STOP_LOSS_PERCENT:
                        exit_msg = f"Stop Loss reached ({STOP_LOSS_PERCENT}%) for {self.symbol}. Exiting position."
                        print(exit_msg)
                        self.send_telegram_message(exit_msg)
                        if self.current_position == "long":
                            amount = self.calculate_position_size(latest_price)
                            self.place_order("sell", amount, latest_price)
                        elif self.current_position == "short":
                            amount = self.calculate_position_size(latest_price)
                            self.place_order("buy", amount, latest_price)
                        full_exit_msg = f"Exited position for {self.symbol}:\nEntry: {self.entry_time.strftime('%Y-%m-%d %H:%M:%S')} at {self.entry_price:.4f}\nExit: {now.strftime('%Y-%m-%d %H:%M:%S')} at {latest_price:.4f}\nProfit: {profit_pct:.2f}%"
                        print(full_exit_msg)
                        self.send_telegram_message(full_exit_msg)
                        self.current_position = None
                        self.entry_price = None
                        self.entry_time = None
                        time.sleep(LOOP_DELAY)
                        continue

                # Если позиции нет и сигнал получен, открываем новую позицию
                if self.current_position is None and signal is not None:
                    sig_msg = f"Signal received for {self.symbol}: {signal.upper()} at price {latest_price:.4f}"
                    print(sig_msg)
                    self.send_telegram_message(sig_msg)
                    amount = self.calculate_position_size(latest_price)
                    if signal == "long":
                        self.place_order("buy", amount, latest_price)
                        self.current_position = "long"
                    elif signal == "short":
                        self.place_order("sell", amount, latest_price)
                        self.current_position = "short"
                    self.entry_price = latest_price
                    self.entry_time = now
                    entry_msg = f"Entered {signal.upper()} position for {self.symbol}:\nTime: {self.entry_time.strftime('%Y-%m-%d %H:%M:%S')}\nPrice: {self.entry_price:.4f}\nPosition size: {amount:.6f} {self.symbol.split('/')[0]}"
                    print(entry_msg)
                    self.send_telegram_message(entry_msg)

                print(f"Current signal for {self.symbol}: {signal}, Position: {self.current_position}, Price: {latest_price:.4f}")

            except Exception as e:
                error_msg = f"Error in bot run for {self.symbol}: {e}"
                print(error_msg)
                self.send_telegram_message(error_msg)
                traceback.print_exc()

            time.sleep(LOOP_DELAY)

if __name__ == "__main__":
    import threading
    from config import SYMBOLS  # SYMBOLS в config.py должны быть списком, например: ["BTC/USDT", "ETH/USDT"]

    bots = []
    threads = []
    for symbol in SYMBOLS:
        bot = MultiTFBot(API_KEY, API_SECRET, API_PASSPHRASE, EXCHANGE_ID, symbol)
        bots.append(bot)
        t = threading.Thread(target=bot.run)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
