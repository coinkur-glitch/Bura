"""Ayarlar ve sinyal geçmişi JSON dosyasında saklanır."""
import json
import os
from threading import Lock
from datetime import datetime

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "data_settings.json")
SIGNALS_FILE  = os.path.join(os.path.dirname(__file__), "data_signals.json")
MAX_SIGNALS   = 200

_lock = Lock()

DEFAULT_SETTINGS = {
    "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"],
    "timeframe": "1h",
    "scan_interval": 60,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "price_alerts": {
        "BTC/USDT": {"above": 100000, "below": 80000},
        "ETH/USDT": {"above": 4000,   "below": 2500},
        "SOL/USDT": {"above": 250,    "below": 100},
    },
    "telegram_token": "",
    "telegram_chat_id": "",
}


def load_settings() -> dict:
    with _lock:
        if not os.path.exists(SETTINGS_FILE):
            return DEFAULT_SETTINGS.copy()
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # eksik anahtarları default ile tamamla
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data


def save_settings(settings: dict):
    with _lock:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)


def load_signals() -> list:
    with _lock:
        if not os.path.exists(SIGNALS_FILE):
            return []
        with open(SIGNALS_FILE, encoding="utf-8") as f:
            return json.load(f)


def append_signal(signal_dict: dict):
    with _lock:
        signals = []
        if os.path.exists(SIGNALS_FILE):
            with open(SIGNALS_FILE, encoding="utf-8") as f:
                signals = json.load(f)
        signal_dict["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signals.insert(0, signal_dict)
        signals = signals[:MAX_SIGNALS]
        with open(SIGNALS_FILE, "w", encoding="utf-8") as f:
            json.dump(signals, f, ensure_ascii=False, indent=2)


def clear_signals():
    with _lock:
        with open(SIGNALS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
