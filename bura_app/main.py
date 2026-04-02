"""
Bura - Satın Alma Talebi Asistanı
Giriş noktası.

Kullanım:
    python main.py

Gereksinimler:
    pip install pywin32 pdfplumber googlesearch-python requests beautifulsoup4
"""

import sys
import os

# bura_app dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

from gui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
