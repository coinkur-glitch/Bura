"""
Tedarikçi sonuçları paneli.
Google araması sonucu bulunan firmaları listeler.
Kullanıcı firma(lar) seçip "Teklif Maili Hazırla" butonuna basabilir.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional

from web_searcher import Supplier


class SupplierPanel(ttk.Frame):
    COLUMNS = ("name", "url", "email", "phone", "product")
    HEADERS = {
        "name": "Firma",
        "url": "Web Sitesi",
        "email": "E-posta",
        "phone": "Telefon",
        "product": "Ürün",
    }
    WIDTHS = {"name": 120, "url": 200, "email": 160, "phone": 110, "product": 140}

    def __init__(
        self,
        parent: tk.Widget,
        on_prepare_email: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self._on_prepare_email = on_prepare_email
        self._suppliers: List[Supplier] = []
        self._build_ui()

    def _build_ui(self):
        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(frm_top, text="Bulunan Tedarikçiler").pack(side=tk.LEFT)
        self._prepare_btn = ttk.Button(
            frm_top,
            text="Teklif Maili Hazırla",
            command=self._prepare_email,
            state=tk.DISABLED,
        )
        self._prepare_btn.pack(side=tk.RIGHT)

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

        self._status_var = tk.StringVar(value="Tedarikçi araması bekleniyor.")
        ttk.Label(self, textvariable=self._status_var, foreground="gray").pack(
            anchor="w", pady=(4, 0)
        )

    def load_suppliers(self, suppliers: List[Supplier]):
        self._suppliers = suppliers
        self._tree.delete(*self._tree.get_children())
        for s in suppliers:
            self._tree.insert(
                "",
                tk.END,
                values=(
                    s.name,
                    s.url,
                    s.email or "-",
                    s.phone or "-",
                    s.product_query,
                ),
            )
        if suppliers:
            self._status_var.set(f"{len(suppliers)} tedarikçi bulundu.")
            self._prepare_btn.configure(state=tk.NORMAL)
        else:
            self._status_var.set("Tedarikçi bulunamadı.")
            self._prepare_btn.configure(state=tk.DISABLED)

    def set_status(self, msg: str):
        self._status_var.set(msg)

    def get_selected_suppliers(self) -> List[Supplier]:
        selected_ids = self._tree.selection()
        if not selected_ids:
            return self._suppliers
        result = []
        for iid in selected_ids:
            idx = self._tree.index(iid)
            result.append(self._suppliers[idx])
        return result

    def _prepare_email(self):
        selected = self.get_selected_suppliers()
        if not selected:
            messagebox.showinfo("Bilgi", "Lütfen en az bir tedarikçi seçin.")
            return
        if self._on_prepare_email:
            self._on_prepare_email(selected)
