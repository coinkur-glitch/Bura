from dataclasses import dataclass, field
from typing import List
import pandas as pd
from config import RSI_OVERSOLD, RSI_OVERBOUGHT, PRICE_ALERTS


@dataclass
class Signal:
    symbol: str
    signal_type: str   # "BUY" | "SELL" | "ALERT"
    reason: str
    price: float
    rsi: float = 0.0
    extra: dict = field(default_factory=dict)

    def __str__(self):
        return (
            f"[{self.signal_type}] {self.symbol} @ {self.price:.4f} | "
            f"RSI: {self.rsi:.1f} | {self.reason}"
        )


def analyze(symbol: str, df: pd.DataFrame) -> List[Signal]:
    if df.empty or len(df) < 2:
        return []

    signals: List[Signal] = []
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["close"])
    current_rsi = float(last["rsi"]) if not pd.isna(last["rsi"]) else 50.0

    # ── RSI Sinyalleri ────────────────────────────────────────────────────
    if current_rsi < RSI_OVERSOLD:
        signals.append(Signal(
            symbol=symbol, signal_type="BUY",
            reason=f"RSI aşırı satım ({current_rsi:.1f} < {RSI_OVERSOLD})",
            price=price, rsi=current_rsi,
        ))
    elif current_rsi > RSI_OVERBOUGHT:
        signals.append(Signal(
            symbol=symbol, signal_type="SELL",
            reason=f"RSI aşırı alım ({current_rsi:.1f} > {RSI_OVERBOUGHT})",
            price=price, rsi=current_rsi,
        ))

    # ── MACD Kesişim ──────────────────────────────────────────────────────
    if (not pd.isna(last["macd"]) and not pd.isna(prev["macd"])):
        macd_cross_up = prev["macd"] < prev["macd_signal"] and last["macd"] > last["macd_signal"]
        macd_cross_dn = prev["macd"] > prev["macd_signal"] and last["macd"] < last["macd_signal"]
        if macd_cross_up:
            signals.append(Signal(
                symbol=symbol, signal_type="BUY",
                reason="MACD yukarı kesişim",
                price=price, rsi=current_rsi,
            ))
        elif macd_cross_dn:
            signals.append(Signal(
                symbol=symbol, signal_type="SELL",
                reason="MACD aşağı kesişim",
                price=price, rsi=current_rsi,
            ))

    # ── Bollinger Band Sinyalleri ─────────────────────────────────────────
    if not pd.isna(last["bb_lower"]) and price < float(last["bb_lower"]):
        signals.append(Signal(
            symbol=symbol, signal_type="BUY",
            reason=f"Fiyat alt BB bandının altında ({float(last['bb_lower']):.4f})",
            price=price, rsi=current_rsi,
        ))
    elif not pd.isna(last["bb_upper"]) and price > float(last["bb_upper"]):
        signals.append(Signal(
            symbol=symbol, signal_type="SELL",
            reason=f"Fiyat üst BB bandının üstünde ({float(last['bb_upper']):.4f})",
            price=price, rsi=current_rsi,
        ))

    # ── Fiyat Alarmları ───────────────────────────────────────────────────
    alert_cfg = PRICE_ALERTS.get(symbol, {})
    if alert_cfg.get("above") and price > alert_cfg["above"]:
        signals.append(Signal(
            symbol=symbol, signal_type="ALERT",
            reason=f"Fiyat alarm seviyesini geçti: {alert_cfg['above']}",
            price=price, rsi=current_rsi,
        ))
    if alert_cfg.get("below") and price < alert_cfg["below"]:
        signals.append(Signal(
            symbol=symbol, signal_type="ALERT",
            reason=f"Fiyat alarm seviyesinin altına düştü: {alert_cfg['below']}",
            price=price, rsi=current_rsi,
        ))

    return signals
