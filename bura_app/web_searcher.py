"""
Web arama modülü.
Ürün adlarına göre Google'da tedarikçi/satıcı araması yapar,
bulunan sitelerde iletişim bilgisi aramaya çalışır.
"""

import re
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse


@dataclass
class Supplier:
    name: str
    url: str
    email: Optional[str] = None
    phone: Optional[str] = None
    product_query: str = ""


class WebSearcher:
    SEARCH_DELAY = 2.5  # Google rate limit için saniye cinsinden bekleme

    def search_suppliers_for_product(
        self, product_name: str, max_results: int = 5
    ) -> List[Supplier]:
        """
        Tek bir ürün için Google'da tedarikçi ara.
        Sonuç bulunamazsa boş liste döner.
        """
        query = f"{product_name} tedarikçi satıcı fiyat Turkey"
        urls = self._google_search(query, max_results)

        suppliers: List[Supplier] = []
        for url in urls:
            site_name = self._extract_site_name(url)
            email, phone = self._scrape_contact(url)
            suppliers.append(
                Supplier(
                    name=site_name,
                    url=url,
                    email=email,
                    phone=phone,
                    product_query=product_name,
                )
            )

        return suppliers

    def search_suppliers_for_products(
        self, product_names: List[str], max_per_product: int = 5,
        progress_callback=None
    ) -> dict:
        """
        Birden fazla ürün için arama yapar.
        Dönen dict: {product_name: [Supplier, ...]}
        progress_callback(current, total, product_name) imzasını kabul eder.
        """
        results = {}
        total = len(product_names)
        for i, name in enumerate(product_names):
            if progress_callback:
                progress_callback(i + 1, total, name)
            results[name] = self.search_suppliers_for_product(name, max_per_product)
            if i < total - 1:
                time.sleep(self.SEARCH_DELAY)
        return results

    def _google_search(self, query: str, max_results: int) -> List[str]:
        try:
            from googlesearch import search
            urls = []
            for url in search(query, num_results=max_results, lang="tr"):
                urls.append(url)
                if len(urls) >= max_results:
                    break
            return urls
        except ImportError:
            raise RuntimeError(
                "googlesearch-python kurulu değil. "
                "Lütfen 'pip install googlesearch-python' çalıştırın."
            )
        except Exception:
            return []

    def _extract_site_name(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            domain = re.sub(r"^www\.", "", domain)
            # alan adının ilk kısmını al (örn. "example.com" → "Example")
            name = domain.split(".")[0].capitalize()
            return name or domain
        except Exception:
            return url

    def _scrape_contact(self, url: str) -> tuple:
        """
        Sayfadan e-posta ve telefon bulmaya çalış.
        Döner: (email | None, phone | None)
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=8)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            email = self._find_email(text)
            phone = self._find_phone(text)
            return email, phone
        except Exception:
            return None, None

    def _find_email(self, text: str) -> Optional[str]:
        pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        matches = re.findall(pattern, text)
        # Görsel/ikon emaillerini filtrele
        filtered = [
            m for m in matches
            if not any(x in m.lower() for x in ["icon", "image", "logo", "pixel"])
        ]
        return filtered[0] if filtered else None

    def _find_phone(self, text: str) -> Optional[str]:
        # Türkiye telefon numarası formatları
        pattern = r"(\+90[\s\-]?)?(\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
        matches = re.findall(pattern, text)
        if matches:
            prefix, number = matches[0]
            return (prefix + number).strip()
        return None
