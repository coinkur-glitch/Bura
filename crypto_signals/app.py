from flask import Flask, render_template, request, jsonify, redirect, url_for
import logging
import storage
import scanner

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ── Sayfalar ─────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/settings")
def settings():
    cfg = storage.load_settings()
    return render_template("settings.html", cfg=cfg)


@app.route("/settings", methods=["POST"])
def settings_save():
    cfg = storage.load_settings()
    cfg["telegram_token"]   = request.form.get("telegram_token", "").strip()
    cfg["telegram_chat_id"] = request.form.get("telegram_chat_id", "").strip()
    cfg["timeframe"]        = request.form.get("timeframe", "1h")
    cfg["scan_interval"]    = int(request.form.get("scan_interval", 60))
    cfg["rsi_oversold"]     = int(request.form.get("rsi_oversold", 30))
    cfg["rsi_overbought"]   = int(request.form.get("rsi_overbought", 70))

    symbols_raw = request.form.get("symbols", "")
    cfg["symbols"] = [s.strip().upper() for s in symbols_raw.split("\n") if s.strip()]

    # Fiyat alarmları
    alerts = {}
    for sym in cfg["symbols"]:
        key = sym.replace("/", "_")
        above = request.form.get(f"alert_above_{key}", "").strip()
        below = request.form.get(f"alert_below_{key}", "").strip()
        entry = {}
        if above:
            entry["above"] = float(above)
        if below:
            entry["below"] = float(below)
        if entry:
            alerts[sym] = entry
    cfg["price_alerts"] = alerts

    storage.save_settings(cfg)
    return redirect(url_for("settings"))


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/signals")
def api_signals():
    return jsonify(storage.load_signals())


@app.route("/api/signals/clear", methods=["POST"])
def api_signals_clear():
    storage.clear_signals()
    return jsonify({"ok": True})


@app.route("/api/prices")
def api_prices():
    return jsonify(scanner.get_prices())


@app.route("/api/scanner/status")
def api_scanner_status():
    return jsonify(scanner.get_status())


@app.route("/api/scanner/start", methods=["POST"])
def api_scanner_start():
    ok = scanner.start()
    return jsonify({"ok": ok, "msg": "Başlatıldı" if ok else "Zaten çalışıyor"})


@app.route("/api/scanner/stop", methods=["POST"])
def api_scanner_stop():
    scanner.stop()
    return jsonify({"ok": True, "msg": "Durduruldu"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050, use_reloader=False)
