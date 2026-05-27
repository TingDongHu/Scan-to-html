#!/usr/bin/env python3
"""Package scan-to-html output into a deliverable zip file.

Usage: python package_output.py [output_name]
Default: output.zip

Packages: index.html (or page_*.html) + all referenced images + pdf_pages/ originals
"""

import sys
import os
import re
import zipfile
from pathlib import Path

def find_html_files(directory):
    """Find all HTML files that look like reconstructed output."""
    html_files = []
    for f in sorted(directory.iterdir()):
        if f.suffix.lower() == '.html' and f.name not in ('index.html',):
            # page_1.html, page_2.html, etc.
            if re.match(r'page_\d+\.html$', f.name):
                html_files.append(f)
    # Also check for a single index.html that's not the template index
    single = directory / 'index.html'
    if single.exists() and not html_files:
        html_files.append(single)
    return html_files

def find_images_in_html(html_content):
    """Extract image paths referenced in HTML."""
    return re.findall(r'src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|svg))["\']', html_content, re.IGNORECASE)

def main():
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    zip_name = sys.argv[2] if len(sys.argv) > 2 else 'output.zip'

    html_files = find_html_files(output_dir)
    if not html_files:
        print("Error: No reconstructed HTML files found (page_*.html)")
        print("  Looked in:", output_dir.resolve())
        sys.exit(1)

    print(f"Found {len(html_files)} HTML file(s):")
    for f in html_files:
        print(f"  {f.name}")

    # Collect all referenced images
    image_files = set()
    for html_file in html_files:
        content = html_file.read_text(encoding='utf-8')
        refs = find_images_in_html(content)
        for ref in refs:
            img_path = output_dir / ref
            if img_path.exists():
                image_files.add(img_path)
            else:
                print(f"  Warning: Referenced image not found: {ref}")

    # Also include pdf_pages/ originals if they exist
    pdf_pages = output_dir / 'pdf_pages'
    pdf_originals = []
    if pdf_pages.is_dir():
        for f in sorted(pdf_pages.iterdir()):
            if f.suffix.lower() == '.png':
                pdf_originals.append(f)

    # Create zip
    zip_path = output_dir / zip_name
    with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add HTML files (first one becomes index.html)
        for i, html_file in enumerate(html_files):
            if i == 0:
                arcname = 'index.html'
            else:
                arcname = html_file.name
            zf.write(str(html_file), arcname)
            print(f"  + {arcname}")

        # Add referenced images
        for img in sorted(image_files):
            arcname = f"images/{img.name}"
            zf.write(str(img), arcname)
            print(f"  + {arcname}")

        # Add original PDF page images
        for orig in pdf_originals:
            arcname = f"originals/{orig.name}"
            zf.write(str(orig), arcname)
            print(f"  + {arcname}")

    size_kb = zip_path.stat().st_size / 1024
    print(f"\nPackaged: {zip_path} ({size_kb:.0f} KB)")
    print(f"  HTML: {len(html_files)}")
    print(f"  Images: {len(image_files)}")
    print(f"  Originals: {len(pdf_originals)}")

if __name__ == "__main__":
    main()
