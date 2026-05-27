#!/usr/bin/env python3
"""Generate preview images for all templates in the templates/ directory.

Usage: python generate_previews.py
Requires: pip install html2image
Also requires Chrome/Chromium/Edge browser installed on the system.
"""

import sys
import os
import shutil
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

TEMPLATE_LIST = [
    "passport",
    "id_card",
    "driver_license",
    "business_card",
    "visa",
    "boarding_pass",
    "hotel_booking",
    "invoice",
    "receipt",
    "quotation",
    "payslip",
    "bank_statement",
    "birth_certificate",
    "diploma",
    "transcript",
    "police_clearance",
    "power_of_attorney",
    "contract",
]

# Browser paths by platform
BROWSER_PATHS = [
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # Linux
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
]

def find_browser():
    for path in BROWSER_PATHS:
        if os.path.exists(path):
            return path
    return None

def main():
    try:
        from html2image import Html2Image
    except ImportError:
        print("Error: html2image not installed. Run: pip install html2image")
        sys.exit(1)

    browser = find_browser()
    if not browser:
        print("Error: No Chrome/Edge browser found on this system.")
        sys.exit(1)

    print(f"Using browser: {browser}")
    hti = Html2Image(output_path=str(TEMPLATES_DIR), browser_executable=browser)

    print(f"Generating previews for {len(TEMPLATE_LIST)} templates...")

    for name in TEMPLATE_LIST:
        template_path = TEMPLATES_DIR / name / "template.html"
        if not template_path.exists():
            print(f"  SKIP: {template_path} not found")
            continue

        html_content = template_path.read_text(encoding="utf-8")

        # Generate screenshot - save to temp name first to avoid path issues
        temp_name = f"_preview_{name}.png"
        hti.screenshot(
            html_str=html_content,
            save_as=temp_name,
            size=(400, 300),
        )

        # Move from templates dir to correct subdirectory
        temp_path = TEMPLATES_DIR / temp_name
        preview_path = TEMPLATES_DIR / name / "preview.png"

        if temp_path.exists():
            shutil.move(str(temp_path), str(preview_path))
            print(f"  OK: {preview_path}")
        else:
            print(f"  WARN: preview not created for {name}")

    print(f"\nDone! Previews saved to {TEMPLATES_DIR}/")

if __name__ == "__main__":
    main()
