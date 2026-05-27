#!/usr/bin/env python3
"""Crop section images from a full-page image based on a skeleton.json.

Usage: python crop_section.py full_page.png skeleton.json [--padding 5] [--output crops/]

For each section in the skeleton, crops the corresponding region from the
full-page image and saves it as {section_id}.jpg in the output directory.
Position coordinates in skeleton are interpreted as percentages of page size.
"""

import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    if len(sys.argv) < 3:
        print("Usage: python crop_section.py full_page.png skeleton.json [--padding N] [--output dir/]")
        sys.exit(1)

    image_path = sys.argv[1]
    skeleton_path = sys.argv[2]

    padding = 5
    output_dir = Path("crops")

    args = sys.argv[3:]
    i = 0
    while i < len(args):
        if args[i] == "--padding" and i + 1 < len(args):
            padding = int(args[i + 1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_dir = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)
    if not os.path.exists(skeleton_path):
        print(f"Error: Skeleton not found: {skeleton_path}")
        sys.exit(1)

    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow not installed. Run: pip install pillow")
        sys.exit(1)

    skeleton = load_json(skeleton_path)
    img = Image.open(image_path)
    pw, ph = img.size
    output_dir.mkdir(parents=True, exist_ok=True)

    sections = skeleton.get("sections", [])
    print(f"Cropping {len(sections)} sections from {pw}x{ph}px image (padding={padding}px)...")

    for sec in sections:
        pos = sec["pos"]
        unit = pos.get("unit", "%")

        if unit == "%":
            x = int(pos["x"] / 100 * pw)
            y = int(pos["y"] / 100 * ph)
            w = int(pos["w"] / 100 * pw)
            h = int(pos["h"] / 100 * ph)
        else:
            x, y, w, h = pos["x"], pos["y"], pos["w"], pos["h"]

        # Apply padding, clamp to image bounds
        x0 = max(0, x - padding)
        y0 = max(0, y - padding)
        x1 = min(pw, x + w + padding)
        y1 = min(ph, y + h + padding)

        crop = img.crop((x0, y0, x1, y1))
        out_path = output_dir / f"{sec['id']}.jpg"
        crop.save(str(out_path), quality=95)
        print(f"  {sec['id']}: ({x0},{y0})-({x1},{y1}) {crop.width}x{crop.height}px -> {out_path}")

    print(f"Done! {len(sections)} sections cropped to {output_dir}/")

if __name__ == "__main__":
    main()
