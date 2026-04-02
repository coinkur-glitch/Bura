"""
Outlook mail gönderme modülü.
win32com üzerinden Outlook 2016 ile teklif isteme maili gönderir.
Hata durumunda Taslaklar klasörüne kaydeder.
"""

from typing import List, Optional
from pdf_parser import Product


MAIL_TEMPLATE = """\
Sayın Yetkili,

Şirketimizin ihtiyaç duyduğu aşağıdaki ürünler için fiyat teklifinizi bekliyoruz.
Tekliflerinizi bu e-posta adresine iletebilirsiniz.

{product_table}

Ürünlerin birim fiyatı, teslim süresi ve ödeme koşullarını da belirtmenizi rica ederiz.

Saygılarımızla,
{sender_name}
"""


def build_mail_body(products: List[Product], sender_name: str = "") -> str:
    """Ürün listesinden mail gövdesi oluşturur."""
    header = f"{'Ürün Kodu':<15} {'Ürün Adı':<40} {'Birim':<10} {'Miktar':<10}"
    separator = "-" * len(header)
    rows = [header, separator]
    for p in products:
        rows.append(
            f"{p.code:<15} {p.name:<40} {p.unit:<10} {p.quantity:<10}"
        )
    table = "\n".join(rows)
    return MAIL_TEMPLATE.format(product_table=table, sender_name=sender_name)


def build_subject(products: List[Product]) -> str:
    """Mail konusunu oluşturur."""
    if len(products) == 1:
        return f"Teklif Talebi - {products[0].name}"
    return f"Teklif Talebi - {len(products)} Kalem Ürün"


class EmailSender:
    def __init__(self):
        self._outlook = None

    def connect(self) -> bool:
        try:
            import win32com.client
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            return True
        except ImportError:
            raise RuntimeError(
                "pywin32 kurulu değil. Lütfen 'pip install pywin32' çalıştırın."
            )
        except Exception as e:
            raise RuntimeError(f"Outlook'a bağlanılamadı: {e}")

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        save_as_draft_on_error: bool = True,
    ) -> bool:
        """
        Maili gönderir. Başarılıysa True, hata durumunda taslağa kaydeder.
        """
        if self._outlook is None:
            self.connect()

        try:
            mail = self._outlook.CreateItem(0)  # 0 = olMailItem
            mail.To = to
            mail.Subject = subject
            mail.Body = body
            if cc:
                mail.CC = cc
            mail.Send()
            return True
        except Exception as send_err:
            if save_as_draft_on_error:
                try:
                    mail.Save()
                except Exception:
                    pass
            raise RuntimeError(
                f"Mail gönderilemedi, Taslaklar'a kaydedildi: {send_err}"
            )

    def get_current_user_email(self) -> str:
        """Aktif Outlook hesabının mail adresini döndürür."""
        try:
            if self._outlook is None:
                self.connect()
            namespace = self._outlook.GetNamespace("MAPI")
            return namespace.CurrentUser.Address or ""
        except Exception:
            return ""

    def get_current_user_name(self) -> str:
        """Aktif Outlook hesabının görünen adını döndürür."""
        try:
            if self._outlook is None:
                self.connect()
            namespace = self._outlook.GetNamespace("MAPI")
            return namespace.CurrentUser.Name or ""
        except Exception:
            return ""
