"""Arka planda çalışan tarayıcı thread'i."""
import time
import logging
import threading
import requests as req_lib
import os

import ccxt
import pandas as pd
import numpy as np

from storage import load_settings, append_signal

logger = logging.getLogger("scanner")

_thread: threading.Thread | None = None
_stop_event = threading.Event()
_status = {"running": False, "last_scan": None, "last_error": None}
_prices: dict = {}
_prices_lock = threading.Lock()


def get_status() -> dict:
    return {**_status, "running": _thread is not None and _thread.is_alive()}


def get_prices() -> dict:
    with _prices_lock:
        return dict(_prices)


# ── İndikatörler ────────────────────────────────────────────────────────────

def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series, fast, slow, sig):
    ema_f = close.ewm(span=fast, adjust=False).mean()
    ema_s = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_f - ema_s
    signal_line = macd_line.ewm(span=sig, adjust=False).mean()
    return macd_line, signal_line


def _bb(close: pd.Series, period, std_mult):
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    return mid + std_mult * std, mid, mid - std_mult * std


# ── Telegram ─────────────────────────────────────────────────────────────────

def _send_telegram(token: str, chat_id: str, text: str):
    if not token or not chat_id:
        return
    try:
        req_lib.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        logger.warning("Telegram gönderilemedi: %s", e)


# ── Tek tarama ───────────────────────────────────────────────────────────────

def _scan_once(cfg: dict):
    exchange = getattr(ccxt, "binance")({"enableRateLimit": True})
    symbols   = cfg["symbols"]
    timeframe = cfg["timeframe"]
    limit     = 100
    rsi_os    = cfg["rsi_oversold"]
    rsi_ob    = cfg["rsi_overbought"]
    alerts    = cfg.get("price_alerts", {})
    tg_token  = cfg.get("telegram_token", "")
    tg_chat   = cfg.get("telegram_chat_id", "")

    for symbol in symbols:
        try:
            raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            ticker = exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error("%s veri alınamadı: %s", symbol, e)
            continue

        price = float(ticker.get("last", 0))
        with _prices_lock:
            _prices[symbol] = {
                "price": price,
                "change": ticker.get("percentage", 0),
            }

        if not raw:
            continue

        df = pd.DataFrame(raw, columns=["ts","open","high","low","close","vol"])
        close = df["close"].astype(float)

        rsi_val   = float(_rsi(close, 14).iloc[-1])
        macd_l, sig_l = _macd(close, 12, 26, 9)
        bb_upper, _, bb_lower = _bb(close, 20, 2.0)

        prev_macd = macd_l.iloc[-2]; prev_sig = sig_l.iloc[-2]
        last_macd = macd_l.iloc[-1]; last_sig = sig_l.iloc[-1]

        candidates = []

        # RSI
        if not pd.isna(rsi_val):
            if rsi_val < rsi_os:
                candidates.append(("BUY",  f"RSI aşırı satım ({rsi_val:.1f})"))
            elif rsi_val > rsi_ob:
                candidates.append(("SELL", f"RSI aşırı alım ({rsi_val:.1f})"))

        # MACD kesişim
        if not any(pd.isna(x) for x in [prev_macd, prev_sig, last_macd, last_sig]):
            if prev_macd < prev_sig and last_macd > last_sig:
                candidates.append(("BUY",  "MACD yukarı kesişim"))
            elif prev_macd > prev_sig and last_macd < last_sig:
                candidates.append(("SELL", "MACD aşağı kesişim"))

        # Bollinger
        bu = float(bb_upper.iloc[-1]); bl = float(bb_lower.iloc[-1])
        if not pd.isna(bl) and price < bl:
            candidates.append(("BUY",  f"Alt BB altında ({bl:.2f})"))
        elif not pd.isna(bu) and price > bu:
            candidates.append(("SELL", f"Üst BB üstünde ({bu:.2f})"))

        # Fiyat alarmları
        al = alerts.get(symbol, {})
        if al.get("above") and price > al["above"]:
            candidates.append(("ALERT", f"Fiyat {al['above']} üstüne çıktı"))
        if al.get("below") and price < al["below"]:
            candidates.append(("ALERT", f"Fiyat {al['below']} altına düştü"))

        emoji = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}
        for stype, reason in candidates:
            sig_dict = {
                "symbol": symbol, "type": stype,
                "reason": reason, "price": price,
                "rsi": round(rsi_val, 1) if not pd.isna(rsi_val) else None,
            }
            append_signal(sig_dict)
            em = emoji.get(stype, "ℹ️")
            msg = (
                f"{em} *{stype}* — {symbol}\n"
                f"💰 Fiyat: `{price:.4f}`\n"
                f"📊 RSI: `{rsi_val:.1f}`\n"
                f"📝 {reason}"
            )
            _send_telegram(tg_token, tg_chat, msg)
            logger.info("%s %s %s @ %.4f | %s", em, stype, symbol, price, reason)


# ── Thread yönetimi ──────────────────────────────────────────────────────────

def _run_loop():
    logger.info("Scanner başlatıldı.")
    _status["running"] = True
    while not _stop_event.is_set():
        try:
            cfg = load_settings()
            _scan_once(cfg)
            _status["last_scan"] = __import__("datetime").datetime.now().strftime("%H:%M:%S")
            _status["last_error"] = None
        except Exception as e:
            _status["last_error"] = str(e)
            logger.error("Tarama hatası: %s", e, exc_info=True)
        interval = load_settings().get("scan_interval", 60)
        _stop_event.wait(interval)
    _status["running"] = False
    logger.info("Scanner durduruldu.")


def start():
    global _thread
    if _thread and _thread.is_alive():
        return False
    _stop_event.clear()
    _thread = threading.Thread(target=_run_loop, daemon=True, name="scanner")
    _thread.start()
    return True


def stop():
    _stop_event.set()
    return True
