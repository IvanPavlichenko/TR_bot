# config.py

# --- API и настройки биржи ---
API_KEY = "dc663dd4-47c0-4a76-878d-2ce9d6688c36"
API_SECRET = "594075EA9CCBD2941914F47850BA624B"
API_PASSPHRASE = "sTL24i8mWSwhS4@"  # OKX требует passphrase

EXCHANGE_ID = "okx"
SYMBOLS = ["BTC/USDT:USDT" ]  # Торговая пара для бессрочного контракта

# "ETH/USDT:USDT"

# --- Таймфреймы и данные ---
TF_SHORT = "15m"   # Короткий таймфрейм для детального анализа
TF_LONG = "4h"     # Длинный таймфрейм для определения тренда
CANDLE_LIMIT = 400  # Количество свечей (покрывает пару дней)

# --- Настройки выполнения ---
LOOP_DELAY = 10  # Задержка между циклами в секундах
IS_PAPERTRADING = False  # True для симуляции, False для реальной торговли

MIN_ORDER_AMOUNT = 0.01  # Минимально допустимый размер заказа для BTC/USDT на OKX

# --- Настройки аккаунта и риск-менеджмента ---
PAPER_BALANCE_USDT = 100.0  # Бумажный баланс
RISK_PER_TRADE = 0.4        # Процент баланса, рискованный на сделку
LEVERAGE = 40               # Плечо для торговли

# --- Параметры фиксации прибыли и стоп‑лосса ---
TAKE_PROFIT_PERCENT = 15.0   # Процент профита для фиксации
STOP_LOSS_PERCENT = -30.0    # Процент убытка для стоп‑лосса (отрицательное значение)

# --- Параметры для ATR и трейлинг-стопа ---
ATR_WINDOW = 14              # Период для расчёта ATR
ATR_MULTIPLIER = 1.5         # Множитель ATR для начального стоп‑лосса
TRAILING_STOP_MULTIPLIER = 1.0  # Множитель ATR для обновления трейлинг‑стопа
FIXED_MARGIN_AMOUNT = 100

# --- Телеграм Бот
TELEGRAM_TOKEN = "8036212595:AAGqc1rVh4RA7nLkPw-psowqskY0ldPVS7c"
TELEGRAM_CHAT_IDS = [1243745632]

LEVERAGE_DICT = {
    "BTC/USDT": 40,   # Плечо для BTC
    "ETH/USDT": 25    # Плечо для ETH (или любое другое значение)
}
DEFAULT_LEVERAGE = 40  # Значение по умолчанию, если пара не указана в словаре