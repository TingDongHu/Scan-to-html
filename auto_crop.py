#!/usr/bin/env python3
"""Auto-crop image into grid regions for scan-to-html inspection.

Usage: python auto_crop.py image.png [rows cols]
Default: 2x2 grid
Output: crops/ directory with numbered regions + grid overlay thumbnail
"""

import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_crop.py image.png [rows cols]")
        print("  rows: default 2")
        print("  cols: default 2")
        sys.exit(1)

    image_path = sys.argv[1]
    try:
        rows = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    except ValueError:
        print("Error: rows must be an integer")
        sys.exit(1)
    try:
        cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    except ValueError:
        print("Error: cols must be an integer")
        sys.exit(1)

    if rows < 1 or cols < 1:
        print("Error: rows and cols must be positive integers (>= 1)")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Error: Pillow not installed. Run: pip install pillow")
        sys.exit(1)

    try:
        img = Image.open(image_path)
        w, h = img.size
    except Exception as e:
        print(f"Error: Could not open image '{image_path}'")
        print(f"  {type(e).__name__}: {e}")
        sys.exit(1)

    output_dir = Path("crops")
    output_dir.mkdir(exist_ok=True)

    # Get base filename for naming
    base_name = Path(image_path).stem

    cell_w = w // cols
    cell_h = h // rows

    print(f"Cropping {w}x{h}px image into {rows}x{cols} grid...")

    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            top = r * cell_h
            right = (c + 1) * cell_w if c < cols - 1 else w
            bottom = (r + 1) * cell_h if r < rows - 1 else h

            crop = img.crop((left, top, right, bottom))
            output_path = output_dir / f"{base_name}_r{r+1}c{c+1}.jpg"
            crop.save(str(output_path), quality=95)
            print(f"  {output_path}: {crop.width}x{crop.height}px")

    # Generate grid overlay thumbnail
    thumb = img.copy()
    thumb.thumbnail((1200, 1200))
    draw = ImageDraw.Draw(thumb)
    scale_x = thumb.width / w
    scale_y = thumb.height / h

    for r in range(1, rows):
        y = int(r * cell_h * scale_y)
        draw.line([(0, y), (thumb.width, y)], fill="red", width=2)

    for c in range(1, cols):
        x = int(c * cell_w * scale_x)
        draw.line([(x, 0), (x, thumb.height)], fill="red", width=2)

    grid_path = output_dir / f"{base_name}_grid.jpg"
    thumb.save(str(grid_path), quality=90)
    print(f"\nGrid overlay: {grid_path}")
    print(f"Done! {rows*cols} regions cropped to {output_dir}/")

if __name__ == "__main__":
    main()
