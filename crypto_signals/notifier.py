import logging
import os
import requests
from signals import Signal
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

EMOJI = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}


def _token() -> str:
    return os.environ.get("TELEGRAM_TOKEN", TELEGRAM_TOKEN)


def _chat_id() -> str:
    return os.environ.get("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)


def send_telegram(signal: Signal) -> bool:
    token = _token()
    chat_id = _chat_id()
    if not token or not chat_id:
        logger.debug("Telegram token/chat_id ayarlanmamış, atlanıyor.")
        return False

    em = EMOJI.get(signal.signal_type, "ℹ️")
    text = (
        f"{em} *{signal.signal_type}* — {signal.symbol}\n"
        f"💰 Fiyat: `{signal.price:.4f}`\n"
        f"📊 RSI: `{signal.rsi:.1f}`\n"
        f"📝 {signal.reason}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Telegram gönderilemedi: %s", e)
        return False


def log_signal(signal: Signal):
    em = EMOJI.get(signal.signal_type, "ℹ️")
    logger.info("%s %s", em, signal)


def notify(signal: Signal):
    log_signal(signal)
    send_telegram(signal)
