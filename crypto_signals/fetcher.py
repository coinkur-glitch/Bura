import ccxt
import pandas as pd
import logging
from config import EXCHANGE, CANDLE_LIMIT

logger = logging.getLogger(__name__)


def get_exchange():
    ex = getattr(ccxt, EXCHANGE)({"enableRateLimit": True})
    return ex


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = CANDLE_LIMIT) -> pd.DataFrame:
    ex = get_exchange()
    try:
        raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except ccxt.NetworkError as e:
        logger.error("Ağ hatası %s %s: %s", symbol, timeframe, e)
        return pd.DataFrame()
    except ccxt.ExchangeError as e:
        logger.error("Borsa hatası %s %s: %s", symbol, timeframe, e)
        return pd.DataFrame()

    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def fetch_ticker(symbol: str) -> dict:
    ex = get_exchange()
    try:
        return ex.fetch_ticker(symbol)
    except (ccxt.NetworkError, ccxt.ExchangeError) as e:
        logger.error("Ticker hatası %s: %s", symbol, e)
        return {}
