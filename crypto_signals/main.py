#!/usr/bin/env python3
"""
Kripto Sinyal Botu
Kullanım: python main.py [--once]
  --once  : Tek tarama yapıp çıkar (sürekli döngü yerine)
"""

import sys
import time
import logging
import logging.handlers

from config import SYMBOLS, TIMEFRAME, SCAN_INTERVAL, LOG_FILE, LOG_LEVEL
from fetcher import fetch_ohlcv
from indicators import add_indicators
from signals import analyze
from notifier import notify


def setup_logging():
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler_console = logging.StreamHandler()
    handler_file = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=fmt,
        handlers=[handler_console, handler_file],
    )


def scan_once():
    logger = logging.getLogger("scanner")
    logger.info("Tarama başlıyor — %d sembol, %s zaman dilimi", len(SYMBOLS), TIMEFRAME)

    found = 0
    for symbol in SYMBOLS:
        df = fetch_ohlcv(symbol, TIMEFRAME)
        if df.empty:
            logger.warning("%s için veri alınamadı, atlanıyor.", symbol)
            continue

        df = add_indicators(df)
        sigs = analyze(symbol, df)

        if not sigs:
            logger.debug("%s: sinyal yok.", symbol)
        for sig in sigs:
            notify(sig)
            found += 1

    logger.info("Tarama tamamlandı — %d sinyal bulundu.", found)


def main():
    setup_logging()
    once = "--once" in sys.argv

    if once:
        scan_once()
        return

    logger = logging.getLogger("main")
    logger.info("Bot başlatıldı. Tarama aralığı: %ds", SCAN_INTERVAL)
    while True:
        try:
            scan_once()
        except KeyboardInterrupt:
            logger.info("Bot durduruldu.")
            break
        except Exception as e:
            logger.error("Beklenmeyen hata: %s", e, exc_info=True)
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
