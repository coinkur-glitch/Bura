# CLAUDE.md

Bu dosya, Claude Code'un (claude.ai/code) bu repoda çalışırken kullanması için hazırlanmıştır.

## Proje Hakkında

**Bura**, yalnızca Windows'ta çalışan, Türkçe bir satın alma talebi asistanıdır. Bir üretim firmasına özgü şu iş akışını otomatikleştirir:

1. Outlook'ta konusu `"A.KAHVECI MIN ALTINA DUSEN STOKLARINIZ LİSTELENMİŞTİR"` içeren e-postaları filtreler
2. PDF eklerini indirip `"SARF MALZEME BEYLIKDUZU FABRIKA"` bölümündeki ürün listesini çıkarır
3. Her ürün için Google'da Türk tedarikçi arar, iletişim bilgilerini toplar
4. Outlook üzerinden teklif isteme maili hazırlayıp gönderir

İki modda çalışır; her ikisi de aynı çekirdek modülleri paylaşır:
- **Masaüstü GUI** (`bura_app/`) — tkinter uygulaması, `BASLA.bat` ile başlatılır
- **Web uygulaması** (`web_app/`) — aynı WiFi'daki telefon/tabletten erişilebilen Flask sunucusu, `WEB_BASLA.bat` ile başlatılır

## Uygulamaları Çalıştırma

**Bağımlılıkları yükle (Windows):**
```
pip install pywin32 pdfplumber googlesearch-python requests beautifulsoup4 flask
```
Ya da Windows'ta `KURULUM.bat` (masaüstü) / `WEB_KURULUM.bat` (web) çalıştırılabilir.

**Masaüstü GUI:**
```
cd bura_app
python main.py
```

**Web sunucusu** (`http://localhost:5000` veya `http://<PC-IP>:5000` ile mobil erişim):
```
cd web_app
python app.py
```

Projede test veya linting yapılandırması bulunmamaktadır.

## Mimari

### Modül Paylaşım Yapısı

`web_app/app.py`, `sys.path`'e `../bura_app` dizinini manuel olarak ekler; böylece her iki giriş noktası da aynı dört çekirdek modülü doğrudan içe aktarır (paket yapısı yoktur):

| Modül | Ana sınıf | Amaç |
|---|---|---|
| `outlook_reader.py` | `OutlookReader` | `win32com.client` ile Outlook'a bağlanır, mailleri filtreler, PDF eklerini geçici dizine kaydeder |
| `pdf_parser.py` | `PDFParser` | `pdfplumber` ile PDF okur; sabit hedef bölümden ürün satırlarını çıkarır |
| `web_searcher.py` | `WebSearcher` | Her ürün için Google araması yapar, sonuç sayfalarından e-posta/telefon bilgisi toplar |
| `email_sender.py` | `EmailSender` + yardımcılar | Outlook COM üzerinden mail gönderir veya taslağa kaydeder; `build_mail_body` / `build_subject` teklif mailini biçimlendirir |

### Yalnızca Windows Kısıtı

`OutlookReader` ve `EmailSender`, `pywin32` ve çalışan bir Outlook 2016+ sürecini zorunlu kılar. Tüm COM çağrıları `win32com.client.Dispatch("Outlook.Application")` üzerinden yapılır. Windows dışı ortamlar için yedek mekanizma yoktur.

### Masaüstü GUI (`bura_app/gui/`)

- `MainWindow` (tkinter `Tk`), dört çekirdek modül örneğine sahiptir ve paneller arası koordinasyonu yönetir.
- Outlook bağlantısı, PDF ayrıştırma ve web araması gibi uzun işlemler her zaman `threading.Thread(daemon=True)` içinde çalışır; sonuçlar `self.after(0, callback)` ile tkinter ana iş parçacığına iletilir.
- `ProductPanel` ve `SupplierPanel`, `ttk.Frame` alt sınıflarıdır; `MainWindow` ile yapım sırasında geçirilen callback fonksiyonları (`on_search_request`, `on_prepare_email`) aracılığıyla iletişir.
- `EmailPreviewDialog` modal bir `tk.Toplevel` penceresidir.

### Web Uygulaması (`web_app/`)

- Dört global örnek (`_reader`, `_parser`, `_searcher`, `_sender`) tüm istekler arasında paylaşılır.
- `_mail_cache` sözlüğü (`entry_id` anahtarlı), iki adımlı akışa köprü kurar: `GET /api/mails` önbelleği doldurur, ardından `GET /api/mail/<id>/products` oradan okur. Her mail yenilemesinde önbellek temizlenir.
- Tedarikçi araması arka planda `threading.Thread` ile çalışır; ilerleme `_search_state` sözlüğünde tutulur ve ön yüz tarafından her 1,5 saniyede `GET /api/search/status` ile sorgulanır.
- Ön yüz (`index.html`), çerçeve veya derleme adımı gerektirmeyen, saf JavaScript ile yazılmış tek dosyalı bir SPA'dır.

### Sabit İş Mantığı Sabitleri

İki sabit, gerçek belge formatlarıyla tam olarak eşleşmek zorundadır:
- `outlook_reader.py:24` — `TARGET_SUBJECT` — mail konusu filtre metni
- `pdf_parser.py:13` — `TARGET_SECTION` — ayrıştırmanın başlayacağı PDF bölüm başlığı

### PDF Ayrıştırma Stratejisi

`PDFParser` önce tablo çıkarımını dener (`pdfplumber` tabloları), başarısız olursa düz metne geçer. Bölüm tespiti büyük harf oranı buluşsal yöntemine dayanır (`_is_section_header`): %70'ten fazla büyük harf ve hiç rakam içermeyen bir satır yeni bölüm başlığı sayılır ve çıkarım durdurulur.

### Google Arama Hız Sınırı

`WebSearcher.SEARCH_DELAY = 2.5` saniye, Google hız sınırını aşmamak için ürünler arasında uygulanır. Çok sayıda ürünü kapsayan aramalar arka plan iş parçacığını dakikalarca meşgul edebilir.
