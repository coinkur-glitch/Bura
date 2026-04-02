"""
Mail önizleme ve onay penceresi.
Kullanıcı mail içeriğini düzenleyebilir, ardından gönderir veya iptal eder.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional

from pdf_parser import Product
from email_sender import EmailSender, build_mail_body, build_subject


class EmailPreviewDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        products: List[Product],
        to_address: str,
        sender_name: str = "",
        on_sent: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self.title("Mail Önizleme & Gönder")
        self.resizable(True, True)
        self.geometry("700x560")
        self.grab_set()  # modal

        self._products = products
        self._on_sent = on_sent
        self._sender = EmailSender()

        self._build_ui(to_address, sender_name)

    def _build_ui(self, to_address: str, sender_name: str):
        pad = {"padx": 10, "pady": 5}

        # -- Alıcı --
        frm_to = ttk.Frame(self)
        frm_to.pack(fill=tk.X, **pad)
        ttk.Label(frm_to, text="Alıcı:", width=10, anchor="w").pack(side=tk.LEFT)
        self._to_var = tk.StringVar(value=to_address)
        ttk.Entry(frm_to, textvariable=self._to_var, width=60).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # -- Konu --
        frm_subj = ttk.Frame(self)
        frm_subj.pack(fill=tk.X, **pad)
        ttk.Label(frm_subj, text="Konu:", width=10, anchor="w").pack(side=tk.LEFT)
        self._subj_var = tk.StringVar(value=build_subject(self._products))
        ttk.Entry(frm_subj, textvariable=self._subj_var, width=60).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # -- Gövde --
        ttk.Label(self, text="İçerik:", anchor="w").pack(fill=tk.X, padx=10)
        self._body_text = tk.Text(self, wrap=tk.WORD, font=("Courier New", 10))
        self._body_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._body_text.insert(
            tk.END, build_mail_body(self._products, sender_name)
        )

        # -- Scrollbar --
        sb = ttk.Scrollbar(self._body_text, command=self._body_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._body_text.configure(yscrollcommand=sb.set)

        # -- Butonlar --
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(frm_btn, text="Gönder", command=self._send).pack(
            side=tk.RIGHT, padx=4
        )
        ttk.Button(frm_btn, text="İptal", command=self.destroy).pack(
            side=tk.RIGHT, padx=4
        )

        self._status_var = tk.StringVar()
        ttk.Label(frm_btn, textvariable=self._status_var, foreground="gray").pack(
            side=tk.LEFT
        )

    def _send(self):
        to = self._to_var.get().strip()
        subject = self._subj_var.get().strip()
        body = self._body_text.get("1.0", tk.END).strip()

        if not to:
            messagebox.showwarning("Uyarı", "Lütfen alıcı adresini girin.", parent=self)
            return
        if not subject:
            messagebox.showwarning("Uyarı", "Lütfen konu başlığını girin.", parent=self)
            return

        self._status_var.set("Gönderiliyor...")
        self.update_idletasks()

        try:
            self._sender.connect()
            self._sender.send(to=to, subject=subject, body=body)
            messagebox.showinfo("Başarılı", "Mail başarıyla gönderildi.", parent=self)
            if self._on_sent:
                self._on_sent(to, subject)
            self.destroy()
        except Exception as e:
            self._status_var.set("")
            messagebox.showerror("Hata", str(e), parent=self)
