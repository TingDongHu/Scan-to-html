#!/usr/bin/env python3
"""Export PDF pages to ultra-high-res PNG images for scan-to-html reconstruction.

Usage: python export_pdf.py input.pdf [zoom_level]
Default zoom: 3 (approximately 4K on A3/Ledger size)
"""

import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python export_pdf.py input.pdf [zoom]")
        print("  zoom: default 3, increase for denser text")
        sys.exit(1)

    pdf_path = sys.argv[1]
    try:
        zoom = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    except ValueError:
        print(f"Error: Invalid zoom value '{sys.argv[2]}'. Must be an integer.")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    try:
        import fitz
    except ImportError:
        print("Error: PyMuPDF not installed. Run: pip install pymupdf")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    try:
        output_dir = Path("pdf_pages")
        output_dir.mkdir(exist_ok=True)

        print(f"Exporting {len(doc)} pages at {zoom}x zoom...")

        for i, page in enumerate(doc):
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            output_path = output_dir / f"page_{i+1}.png"
            pix.save(str(output_path))
            print(f"  Page {i+1}: {pix.width}x{pix.height}px -> {output_path}")

        print(f"\nDone! {len(doc)} pages exported to {output_dir}/")
    finally:
        doc.close()

if __name__ == "__main__":
    main()
