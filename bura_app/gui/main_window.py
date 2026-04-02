"""
Ana uygulama penceresi.
Sol panel: mail listesi
Sağ panel: Ürünler (tab 1) + Tedarikçiler (tab 2)
Alt bar: durum çubuğu + ilerleme
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from outlook_reader import OutlookReader, MailItem
from pdf_parser import PDFParser, Product
from web_searcher import WebSearcher, Supplier
from email_sender import EmailSender
from gui.product_panel import ProductPanel
from gui.supplier_panel import SupplierPanel
from gui.email_preview import EmailPreviewDialog


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bura - Satın Alma Talebi Asistanı")
        self.geometry("1100x650")
        self.minsize(800, 500)

        self._reader = OutlookReader()
        self._parser = PDFParser()
        self._searcher = WebSearcher()
        self._sender = EmailSender()

        self._mails: List[MailItem] = []
        self._current_products: List[Product] = []
        self._current_suppliers: List[Supplier] = []

        self._build_ui()
        self.after(200, self._load_mails)

    # ------------------------------------------------------------------
    # UI kurulumu
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Ana pane
        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Sol: mail listesi
        frm_left = ttk.Frame(pane, width=280)
        pane.add(frm_left, weight=1)
        self._build_mail_list(frm_left)

        # Sağ: sekmeli panel
        frm_right = ttk.Frame(pane)
        pane.add(frm_right, weight=3)
        self._build_right_panel(frm_right)

        # Alt durum çubuğu
        self._build_status_bar()

    def _build_mail_list(self, parent: tk.Widget):
        ttk.Label(parent, text="Gelen Mailler").pack(anchor="w", pady=(0, 4))

        frm = ttk.Frame(parent)
        frm.pack(fill=tk.BOTH, expand=True)

        self._mail_tree = ttk.Treeview(
            frm, columns=("date", "sender"), show="headings", selectmode="browse"
        )
        self._mail_tree.heading("date", text="Tarih")
        self._mail_tree.heading("sender", text="Gönderen")
        self._mail_tree.column("date", width=90, anchor="w")
        self._mail_tree.column("sender", width=140, anchor="w")

        vsb = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=self._mail_tree.yview)
        self._mail_tree.configure(yscrollcommand=vsb.set)
        self._mail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._mail_tree.bind("<<TreeviewSelect>>", self._on_mail_select)

        ttk.Button(parent, text="Yenile", command=self._load_mails).pack(
            fill=tk.X, pady=(6, 0)
        )

    def _build_right_panel(self, parent: tk.Widget):
        self._notebook = ttk.Notebook(parent)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Ürünler
        tab_products = ttk.Frame(self._notebook)
        self._notebook.add(tab_products, text="Ürünler")
        self._product_panel = ProductPanel(
            tab_products, on_search_request=self._start_supplier_search
        )
        self._product_panel.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Tab 2: Tedarikçiler
        tab_suppliers = ttk.Frame(self._notebook)
        self._notebook.add(tab_suppliers, text="Tedarikçiler")
        self._supplier_panel = SupplierPanel(
            tab_suppliers, on_prepare_email=self._open_email_preview
        )
        self._supplier_panel.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _build_status_bar(self):
        frm_status = ttk.Frame(self, relief=tk.SUNKEN)
        frm_status.pack(fill=tk.X, side=tk.BOTTOM)

        self._status_var = tk.StringVar(value="Hazır")
        ttk.Label(frm_status, textvariable=self._status_var, anchor="w").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4
        )
        self._progress = ttk.Progressbar(
            frm_status, mode="indeterminate", length=120
        )
        self._progress.pack(side=tk.RIGHT, padx=4, pady=2)

    # ------------------------------------------------------------------
    # Mail yükleme
    # ------------------------------------------------------------------

    def _load_mails(self):
        self._set_status("Outlook'a bağlanılıyor...", busy=True)

        def worker():
            try:
                self._reader.connect()
                mails = self._reader.get_filtered_mails()
                self.after(0, lambda: self._on_mails_loaded(mails))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_mails_loaded(self, mails: List[MailItem]):
        self._mails = mails
        self._mail_tree.delete(*self._mail_tree.get_children())
        for mail in mails:
            date_str = mail.received_time.strftime("%d.%m.%Y")
            self._mail_tree.insert(
                "", tk.END, values=(date_str, mail.sender)
            )
        count = len(mails)
        self._set_status(
            f"{count} mail bulundu." if count else "Eşleşen mail bulunamadı.",
            busy=False,
        )

    # ------------------------------------------------------------------
    # Mail seçimi → PDF ayrıştırma
    # ------------------------------------------------------------------

    def _on_mail_select(self, _event=None):
        selection = self._mail_tree.selection()
        if not selection:
            return
        idx = self._mail_tree.index(selection[0])
        mail = self._mails[idx]

        if not mail.attachments:
            self._product_panel.set_status("Bu mailde PDF eki bulunamadı.")
            self._product_panel.load_products([])
            return

        self._set_status("PDF ayrıştırılıyor...", busy=True)

        def worker():
            try:
                all_products: List[Product] = []
                for pdf_path in mail.attachments:
                    all_products.extend(self._parser.parse(pdf_path))
                self.after(0, lambda: self._on_products_parsed(all_products))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_products_parsed(self, products: List[Product]):
        self._current_products = products
        self._product_panel.load_products(products)
        self._set_status(
            f"{len(products)} ürün ayrıştırıldı." if products else "PDF'de ürün bulunamadı.",
            busy=False,
        )
        self._notebook.select(0)

    # ------------------------------------------------------------------
    # Tedarikçi araması
    # ------------------------------------------------------------------

    def _start_supplier_search(self, products: List[Product]):
        if not products:
            messagebox.showinfo("Bilgi", "Aramak için ürün bulunamadı.")
            return

        self._set_status("Tedarikçiler aranıyor...", busy=True)
        self._supplier_panel.set_status("Arama yapılıyor...")
        self._notebook.select(1)

        product_names = [p.name for p in products if p.name]

        def progress_cb(current, total, name):
            self.after(
                0,
                lambda: self._set_status(
                    f"Aranıyor ({current}/{total}): {name}", busy=True
                ),
            )

        def worker():
            try:
                results_dict = self._searcher.search_suppliers_for_products(
                    product_names, progress_callback=progress_cb
                )
                all_suppliers: List[Supplier] = []
                for suppliers in results_dict.values():
                    all_suppliers.extend(suppliers)
                self.after(0, lambda: self._on_suppliers_found(all_suppliers))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_suppliers_found(self, suppliers: List[Supplier]):
        self._current_suppliers = suppliers
        self._supplier_panel.load_suppliers(suppliers)
        self._set_status(
            f"{len(suppliers)} tedarikçi bulundu." if suppliers else "Tedarikçi bulunamadı.",
            busy=False,
        )

    # ------------------------------------------------------------------
    # Mail önizleme / gönderim
    # ------------------------------------------------------------------

    def _open_email_preview(self, suppliers: List[Supplier]):
        if not self._current_products:
            messagebox.showwarning("Uyarı", "Önce ürün listesi yüklenmeli.")
            return

        # Firma mail adreslerini al; yoksa boş bırak
        to_addresses = [s.email for s in suppliers if s.email]
        to_str = "; ".join(to_addresses) if to_addresses else ""

        try:
            sender_name = self._sender.get_current_user_name()
        except Exception:
            sender_name = ""

        EmailPreviewDialog(
            self,
            products=self._current_products,
            to_address=to_str,
            sender_name=sender_name,
            on_sent=self._on_mail_sent,
        )

    def _on_mail_sent(self, to: str, subject: str):
        self._set_status(f"Mail gönderildi → {to}", busy=False)

    # ------------------------------------------------------------------
    # Yardımcı
    # ------------------------------------------------------------------

    def _set_status(self, msg: str, busy: bool = False):
        self._status_var.set(msg)
        if busy:
            self._progress.start(12)
        else:
            self._progress.stop()

    def _on_error(self, msg: str):
        self._set_status(f"Hata: {msg}", busy=False)
        messagebox.showerror("Hata", msg)
