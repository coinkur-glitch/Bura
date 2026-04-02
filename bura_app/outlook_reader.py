"""
Outlook 2016 mail okuma modülü.
win32com aracılığıyla Outlook'a bağlanır, belirli konu başlıklı
mailleri filtreler ve PDF eklerini geçici dizine kaydeder.
"""

import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class MailItem:
    entry_id: str
    subject: str
    sender: str
    received_time: datetime
    body: str
    attachments: List[str] = field(default_factory=list)  # geçici dosya yolları


TARGET_SUBJECT = "A.KAHVECI MIN ALTINA DUSEN STOKLARINIZ LİSTELENMİŞTİR"


class OutlookReader:
    def __init__(self):
        self._outlook = None
        self._namespace = None
        self._temp_dir = tempfile.mkdtemp(prefix="bura_")

    def connect(self) -> bool:
        """Outlook COM nesnesine bağlan. True dönerse bağlantı başarılı."""
        try:
            import win32com.client
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            self._namespace = self._outlook.GetNamespace("MAPI")
            return True
        except ImportError:
            raise RuntimeError(
                "pywin32 kurulu değil. Lütfen 'pip install pywin32' komutunu çalıştırın."
            )
        except Exception as e:
            raise RuntimeError(f"Outlook'a bağlanılamadı: {e}")

    def get_filtered_mails(self, max_count: int = 50) -> List[MailItem]:
        """
        Gelen kutusundan TARGET_SUBJECT ile eşleşen mailleri döndürür.
        PDF ekleri geçici dizine kaydedilir.
        """
        if self._namespace is None:
            raise RuntimeError("Önce connect() çağrılmalı.")

        inbox = self._namespace.GetDefaultFolder(6)  # 6 = Inbox
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)  # en yeni önce

        results: List[MailItem] = []

        for msg in messages:
            try:
                if TARGET_SUBJECT.lower() not in msg.Subject.lower():
                    continue

                pdf_paths = self._save_pdf_attachments(msg)

                mail = MailItem(
                    entry_id=msg.EntryID,
                    subject=msg.Subject,
                    sender=msg.SenderName,
                    received_time=msg.ReceivedTime,
                    body=msg.Body,
                    attachments=pdf_paths,
                )
                results.append(mail)

                if len(results) >= max_count:
                    break
            except Exception:
                continue

        return results

    def _save_pdf_attachments(self, msg) -> List[str]:
        """Mesajdaki PDF eklerini geçici dizine kaydet ve yollarını döndür."""
        saved: List[str] = []
        try:
            for att in msg.Attachments:
                if att.FileName.lower().endswith(".pdf"):
                    dest = os.path.join(self._temp_dir, att.FileName)
                    # Aynı isimde dosya varsa üzerine yaz
                    att.SaveAsFile(dest)
                    saved.append(dest)
        except Exception:
            pass
        return saved

    def cleanup(self):
        """Geçici PDF dosyalarını temizle."""
        import shutil
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
