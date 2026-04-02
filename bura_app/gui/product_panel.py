"""
Ürün listesi paneli.
Seçilen maildeki PDF'den çıkarılan ürünleri tablo olarak gösterir.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional

from pdf_parser import Product


class ProductPanel(ttk.Frame):
    COLUMNS = ("code", "name", "unit", "quantity")
    HEADERS = {"code": "Kod", "name": "Ürün Adı", "unit": "Birim", "quantity": "Miktar"}
    WIDTHS = {"code": 100, "name": 280, "unit": 70, "quantity": 70}

    def __init__(self, parent: tk.Widget, on_search_request: Optional[Callable] = None):
        super().__init__(parent)
        self._on_search_request = on_search_request
        self._products: List[Product] = []
        self._build_ui()

    def _build_ui(self):
        # Başlık + buton satırı
        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(frm_top, text="Ürün Listesi (SARF MALZEME BEYLIKDUZU FABRIKA)").pack(
            side=tk.LEFT
        )
        self._search_btn = ttk.Button(
            frm_top,
            text="Tedarikçi Ara",
            command=self._request_search,
            state=tk.DISABLED,
        )
        self._search_btn.pack(side=tk.RIGHT)

        # Treeview
        frm_tree = ttk.Frame(self)
        frm_tree.pack(fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(
            frm_tree,
            columns=self.COLUMNS,
            show="headings",
            selectmode="extended",
        )
        for col in self.COLUMNS:
            self._tree.heading(col, text=self.HEADERS[col])
            self._tree.column(col, width=self.WIDTHS[col], anchor="w")

        vsb = ttk.Scrollbar(frm_tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Durum etiketi
        self._status_var = tk.StringVar(value="Mail seçin.")
        ttk.Label(self, textvariable=self._status_var, foreground="gray").pack(
            anchor="w", pady=(4, 0)
        )

    def load_products(self, products: List[Product]):
        self._products = products
        self._tree.delete(*self._tree.get_children())
        for p in products:
            self._tree.insert(
                "", tk.END, values=(p.code, p.name, p.unit, p.quantity)
            )
        if products:
            self._status_var.set(f"{len(products)} ürün bulundu.")
            self._search_btn.configure(state=tk.NORMAL)
        else:
            self._status_var.set("Bu PDF'de ürün bulunamadı.")
            self._search_btn.configure(state=tk.DISABLED)

    def set_status(self, msg: str):
        self._status_var.set(msg)

    def get_selected_products(self) -> List[Product]:
        selected_ids = self._tree.selection()
        if not selected_ids:
            return self._products  # hiçbiri seçilmemişse tümünü döndür
        result = []
        for iid in selected_ids:
            idx = self._tree.index(iid)
            result.append(self._products[idx])
        return result

    def _request_search(self):
        if self._on_search_request:
            self._on_search_request(self.get_selected_products())
