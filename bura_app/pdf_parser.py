"""
PDF ayrıştırma modülü.
pdfplumber kullanarak PDF'teki "SARF MALZEME BEYLIKDUZU FABRIKA"
başlığı altındaki ürün listesini çıkarır.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


TARGET_SECTION = "SARF MALZEME BEYLIKDUZU FABRIKA"


@dataclass
class Product:
    code: str
    name: str
    unit: str
    quantity: str
    raw_line: str


class PDFParser:
    def parse(self, pdf_path: str) -> List[Product]:
        """
        PDF dosyasını okur, TARGET_SECTION altındaki ürünleri döndürür.
        Hata durumunda boş liste döner.
        """
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError(
                "pdfplumber kurulu değil. Lütfen 'pip install pdfplumber' çalıştırın."
            )

        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text_lines = self._extract_all_lines(pdf)
                return self._extract_section_products(all_text_lines)
        except Exception as e:
            raise RuntimeError(f"PDF okunamadı ({pdf_path}): {e}")

    def _extract_all_lines(self, pdf) -> List[str]:
        lines = []
        for page in pdf.pages:
            # Önce tablo olarak dene
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if row:
                            clean = [cell.strip() if cell else "" for cell in row]
                            lines.append("\t".join(clean))
            else:
                # Düz metin
                text = page.extract_text()
                if text:
                    lines.extend(text.splitlines())
        return lines

    def _extract_section_products(self, lines: List[str]) -> List[Product]:
        """
        TARGET_SECTION başlığından sonraki ürün satırlarını ayrıştır.
        Bir sonraki büyük bölüm başlığına gelince dur.
        """
        in_section = False
        products: List[Product] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Bölüm başlığını ara (büyük/küçük harf duyarsız)
            if TARGET_SECTION.lower() in stripped.lower():
                in_section = True
                continue

            if not in_section:
                continue

            # Yeni bir büyük bölüm başlığına geçildiyse dur
            # (Hepsi büyük harf + belirli uzunluk heuristic)
            if self._is_section_header(stripped):
                break

            product = self._parse_product_line(stripped)
            if product:
                products.append(product)

        return products

    def _is_section_header(self, line: str) -> bool:
        """
        Büyük harfli bölüm başlığı tespiti.
        En az 10 karakter, büyük harf oranı yüksek, rakam içermiyor.
        """
        if len(line) < 10:
            return False
        upper_ratio = sum(1 for c in line if c.isupper()) / max(len(line), 1)
        has_digit = any(c.isdigit() for c in line)
        return upper_ratio > 0.7 and not has_digit

    def _parse_product_line(self, line: str) -> Optional[Product]:
        """
        Ürün satırını ayrıştır.
        Beklenen format (tab veya çoklu boşlukla ayrılmış):
          KOD  ÜRÜN_ADI  BİRİM  MİKTAR
        veya sadece metin kolonları.
        """
        # Tab ile ayrılmış (tablo çıktısı)
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
        else:
            # Birden fazla boşlukla ayrılmış
            parts = re.split(r"\s{2,}", line.strip())

        if len(parts) < 2:
            return None

        # İlk kısım ürün kodu gibi görünüyor mu?
        code = parts[0] if len(parts) >= 1 else ""
        name = parts[1] if len(parts) >= 2 else ""
        unit = parts[2] if len(parts) >= 3 else ""
        quantity = parts[3] if len(parts) >= 4 else ""

        # Anlamsız satırları filtrele
        if not name or len(name) < 2:
            return None

        return Product(
            code=code,
            name=name,
            unit=unit,
            quantity=quantity,
            raw_line=line,
        )
