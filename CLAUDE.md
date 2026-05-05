# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**Bura** is a Windows-only Turkish-language procurement assistant ("Satın Alma Talebi Asistanı"). It automates a specific workflow for a manufacturing company:

1. Read Outlook emails whose subject contains `"A.KAHVECI MIN ALTINA DUSEN STOKLARINIZ LİSTELENMİŞTİR"`
2. Extract PDF attachments and parse the `"SARF MALZEME BEYLIKDUZU FABRIKA"` section for a product list
3. Google-search for Turkish suppliers for each product
4. Compose and send quote-request emails via Outlook

It ships in two modes that share the same core modules:
- **Desktop GUI** (`bura_app/`) — tkinter app launched via `BASLA.bat`
- **Web app** (`web_app/`) — Flask server accessible from phones/tablets on the same WiFi, launched via `WEB_BASLA.bat`

## Running the Applications

**Install dependencies (Windows):**
```
pip install pywin32 pdfplumber googlesearch-python requests beautifulsoup4 flask
```
Or run `KURULUM.bat` (desktop) / `WEB_KURULUM.bat` (web) on Windows.

**Desktop GUI:**
```
cd bura_app
python main.py
```

**Web server** (accessible at `http://localhost:5000`, or `http://<PC-IP>:5000` from mobile):
```
cd web_app
python app.py
```

There are no tests or linting configurations in this project.

## Architecture

### Module Sharing Pattern

`web_app/app.py` manually adds `../bura_app` to `sys.path`, so both entry points import the same four core modules directly by filename (not as a package):

| Module | Key class | Purpose |
|---|---|---|
| `outlook_reader.py` | `OutlookReader` | Connects to Outlook via `win32com.client`, filters mails, saves PDF attachments to a temp dir |
| `pdf_parser.py` | `PDFParser` | Parses PDFs with `pdfplumber`; extracts product rows from the hardcoded target section |
| `web_searcher.py` | `WebSearcher` | Google-searches per product, scrapes contact info (email/phone) from result pages |
| `email_sender.py` | `EmailSender` + helpers | Sends or saves-as-draft via Outlook COM; `build_mail_body` / `build_subject` format the quote email |

### Windows-Only Constraint

`OutlookReader` and `EmailSender` both require `pywin32` and a running Outlook 2016+ process. All COM calls are in `win32com.client.Dispatch("Outlook.Application")`. There is no fallback for non-Windows environments.

### Desktop GUI (`bura_app/gui/`)

- `MainWindow` (tkinter `Tk`) owns all four core module instances and coordinates the panels.
- Long operations (Outlook connect, PDF parse, web search) always run in `threading.Thread(daemon=True)` and post results back via `self.after(0, callback)` to stay thread-safe with tkinter.
- `ProductPanel` and `SupplierPanel` are `ttk.Frame` subclasses; they communicate back to `MainWindow` through callback functions (`on_search_request`, `on_prepare_email`) passed at construction time.
- `EmailPreviewDialog` is a modal `tk.Toplevel`.

### Web App (`web_app/`)

- Four global instances (`_reader`, `_parser`, `_searcher`, `_sender`) are shared across all requests.
- A `_mail_cache` dict (keyed by `entry_id`) bridges the two-step flow: `GET /api/mails` populates it, then `GET /api/mail/<id>/products` reads from it. The cache is cleared on each mail refresh.
- Supplier search runs in a background `threading.Thread`; progress is tracked in `_search_state` (a plain dict) and polled by the frontend at `GET /api/search/status` every 1.5 seconds.
- The frontend (`index.html`) is a single-file SPA with vanilla JS and a 4-step stepper — no framework or build step.

### Hardcoded Business Constants

Two constants must match the actual document formats exactly:
- `outlook_reader.py:24` — `TARGET_SUBJECT` — email subject filter string
- `pdf_parser.py:13` — `TARGET_SECTION` — PDF section heading to start parsing from

### PDF Parsing Strategy

`PDFParser` tries table extraction first (`pdfplumber` tables), then falls back to plain text. Section detection uses an uppercase-ratio heuristic (`_is_section_header`): ≥70% uppercase characters and no digits signals a new section header, stopping extraction.

### Google Search Rate Limiting

`WebSearcher.SEARCH_DELAY = 2.5` seconds is applied between products to avoid hitting Google rate limits. Long searches (many products) will block the background thread for minutes.
