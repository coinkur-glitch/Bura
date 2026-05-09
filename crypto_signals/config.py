# Kripto sinyal botu konfigürasyonu

# İzlenecek semboller (Binance formatı)
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
]

# Zaman dilimi: 1m, 5m, 15m, 1h, 4h, 1d
TIMEFRAME = "1h"

# Kaç mum geçmişi çekilsin
CANDLE_LIMIT = 100

# Tarama aralığı (saniye)
SCAN_INTERVAL = 60

# Borsa (ccxt destekli, public endpoint)
EXCHANGE = "binance"

# ── Teknik indikatör parametreleri ──────────────────────────────────────────
RSI_PERIOD = 14
RSI_OVERSOLD = 30     # Bu altına düşünce AL sinyali
RSI_OVERBOUGHT = 70   # Bu üstüne çıkınca SAT sinyali

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_STD = 2.0

# ── Fiyat alarmları ─────────────────────────────────────────────────────────
# Format: {"SEMBOL": {"above": fiyat, "below": fiyat}}
# above: fiyat bu seviyeyi geçerse alarm
# below: fiyat bu seviyenin altına düşerse alarm
PRICE_ALERTS = {
    "BTC/USDT": {"above": 100000, "below": 80000},
    "ETH/USDT": {"above": 4000,   "below": 2500},
    "SOL/USDT": {"above": 250,    "below": 100},
}

# ── Telegram ─────────────────────────────────────────────────────────────────
# .env dosyasından veya buradan ayarlanabilir
# TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID çevre değişkeni olarak da verilebilir
TELEGRAM_TOKEN = ""    # BotFather'dan alınan token
TELEGRAM_CHAT_ID = ""  # Mesaj gönderilecek chat ID

# ── Log ──────────────────────────────────────────────────────────────────────
LOG_FILE = "signals.log"
LOG_LEVEL = "INFO"
