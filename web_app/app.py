"""
Bura Web Uygulaması - Flask Backend
Aynı WiFi'daki tüm cihazlardan (telefon, tablet) erişilebilir.

Başlatmak için: python app.py
Tarayıcıdan: http://localhost:5000  (PC'den)
             http://<PC-IP>:5000   (telefon/tablet'ten, aynı WiFi)
"""

import os
import sys
import threading

from flask import Flask, jsonify, render_template, request

# bura_app modüllerini path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bura_app"))

from outlook_reader import OutlookReader
from pdf_parser import PDFParser
from web_searcher import WebSearcher
from email_sender import EmailSender, build_mail_body, build_subject

app = Flask(__name__)

# Tek bir global instance — uygulama boyunca paylaşılır
_reader = OutlookReader()
_parser = PDFParser()
_searcher = WebSearcher()
_sender = EmailSender()

# Mail önbelleği (entry_id → MailItem)
_mail_cache: dict = {}

# Arama durumu (ilerleme takibi için)
_search_state = {"running": False, "progress": "", "done": False, "results": []}


# ──────────────────────────────────────────────
# Sayfa
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ──────────────────────────────────────────────
# API: Mailler
# ──────────────────────────────────────────────

@app.route("/api/mails")
def api_mails():
    try:
        _reader.connect()
        mails = _reader.get_filtered_mails(max_count=50)
        _mail_cache.clear()
        result = []
        for m in mails:
            _mail_cache[m.entry_id] = m
            result.append({
                "id": m.entry_id,
                "subject": m.subject,
                "sender": m.sender,
                "date": m.received_time.strftime("%d.%m.%Y %H:%M"),
                "has_pdf": len(m.attachments) > 0,
            })
        return jsonify({"ok": True, "mails": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ──────────────────────────────────────────────
# API: PDF'den ürün listesi
# ──────────────────────────────────────────────

@app.route("/api/mail/<mail_id>/products")
def api_products(mail_id: str):
    mail = _mail_cache.get(mail_id)
    if not mail:
        return jsonify({"ok": False, "error": "Mail bulunamadı. Önce mailleri yenileyin."}), 404

    if not mail.attachments:
        return jsonify({"ok": False, "error": "Bu mailde PDF eki yok."}), 400

    try:
        products = []
        for pdf_path in mail.attachments:
            products.extend(_parser.parse(pdf_path))

        result = [
            {"code": p.code, "name": p.name, "unit": p.unit, "quantity": p.quantity}
            for p in products
        ]
        return jsonify({"ok": True, "products": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ──────────────────────────────────────────────
# API: Tedarikçi araması (arka planda)
# ──────────────────────────────────────────────

@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    product_names = data.get("products", [])
    if not product_names:
        return jsonify({"ok": False, "error": "Ürün listesi boş."}), 400

    if _search_state["running"]:
        return jsonify({"ok": False, "error": "Arama zaten devam ediyor."}), 409

    _search_state.update({"running": True, "progress": "Başlıyor...", "done": False, "results": []})

    def worker():
        def on_progress(current, total, name):
            _search_state["progress"] = f"Aranıyor ({current}/{total}): {name}"

        try:
            results_dict = _searcher.search_suppliers_for_products(
                product_names, progress_callback=on_progress
            )
            all_suppliers = []
            for suppliers in results_dict.values():
                for s in suppliers:
                    all_suppliers.append({
                        "name": s.name,
                        "url": s.url,
                        "email": s.email or "",
                        "phone": s.phone or "",
                        "product": s.product_query,
                    })
            _search_state.update({"running": False, "done": True, "results": all_suppliers, "progress": "Tamamlandı."})
        except Exception as e:
            _search_state.update({"running": False, "done": True, "results": [], "progress": f"Hata: {e}"})

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok": True, "message": "Arama başlatıldı."})


@app.route("/api/search/status")
def api_search_status():
    return jsonify({
        "running": _search_state["running"],
        "progress": _search_state["progress"],
        "done": _search_state["done"],
        "results": _search_state["results"] if _search_state["done"] else [],
    })


# ──────────────────────────────────────────────
# API: Mail gönder
# ──────────────────────────────────────────────

@app.route("/api/send-email", methods=["POST"])
def api_send_email():
    data = request.get_json()
    to = data.get("to", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()

    if not to:
        return jsonify({"ok": False, "error": "Alıcı adresi boş."}), 400
    if not subject:
        return jsonify({"ok": False, "error": "Konu boş."}), 400
    if not body:
        return jsonify({"ok": False, "error": "Mail içeriği boş."}), 400

    try:
        _sender.connect()
        _sender.send(to=to, subject=subject, body=body)
        return jsonify({"ok": True, "message": f"Mail gönderildi → {to}"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ──────────────────────────────────────────────
# API: Mail taslağı oluştur
# ──────────────────────────────────────────────

@app.route("/api/draft", methods=["POST"])
def api_draft():
    data = request.get_json()
    products_raw = data.get("products", [])

    from pdf_parser import Product
    products = [
        Product(
            code=p.get("code", ""),
            name=p.get("name", ""),
            unit=p.get("unit", ""),
            quantity=p.get("quantity", ""),
            raw_line="",
        )
        for p in products_raw
    ]

    try:
        _sender.connect()
        sender_name = _sender.get_current_user_name()
    except Exception:
        sender_name = ""

    return jsonify({
        "ok": True,
        "subject": build_subject(products),
        "body": build_mail_body(products, sender_name),
    })


if __name__ == "__main__":
    # 0.0.0.0 → aynı WiFi'daki tüm cihazlardan erişilebilir
    print("\n" + "="*50)
    print("  BURA Web Uygulaması Başlatıldı!")
    print("  PC'den:     http://localhost:5000")
    print("  Telefondan: http://<PC-IP-ADRESI>:5000")
    print("  (PC'nin IP'si için: cmd → ipconfig)")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
