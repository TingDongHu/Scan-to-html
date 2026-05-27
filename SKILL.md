---
name: scan-to-html
description: Use when converting image-based PDFs, scanned documents, or raster drawings into structured HTML with preserved layout and text content. Triggers when PDF text extraction returns empty, garbled, or incomplete; when document contains tables, diagrams, or multi-column layouts that must be visually reconstructed; when source is a scan, photo, or image-exported PDF rather than text-native.
---

# Scan to HTML Reconstruction

## Overview

Rebuild scanned or image-based documents as static HTML by treating the source as visual data, not text. The entire workflow depends on one prerequisite: ultra-high-resolution image export. If the image is not sharp enough to read every character, no amount of zoom or OCR will recover it reliably.

## When to Use

- PDF `Read` returns empty, garbled, or unusable text
- Document contains tables, engineering diagrams, or precise layouts
- Content is a scan, photograph, or raster image embedded in PDF
- Need to preserve visual structure (columns, alignment, whitespace)

## Prerequisites

```bash
pip install pymupdf pillow html2image
npm install -g mineru-open-api
```

- **PyMuPDF** (`pymupdf`): PDF to high-res image export
- **Pillow** (`pillow`): Image cropping and inspection
- **html2image**: Preview generation (requires Chrome, Chromium, or Edge browser installed)
- **mineru-open-api**: MinerU document extraction CLI (see MinerU-Enhanced Workflow)

## Core Workflow

**Step 1 — Export 4K-resolution images**

This is non-negotiable. Use PyMuPDF (fitz) with at least 2× zoom, preferably 3–4× for dense text.

```python
import fitz
doc = fitz.open('file.pdf')
page = doc[0]
mat = fitz.Matrix(3, 3)  # 3x = ~4K on A3/Ledger size
pix = page.get_pixmap(matrix=mat)
pix.save('page_1.png')
```

If the exported image is still blurry, increase zoom until every character is legible at 1:1 zoom. A low-res export makes every downstream step impossible.

**Step 2 — Analyze global structure before extracting text**

Open the full image and identify:
- Number of pages
- Table row/column structure (including colspan/rowspan)
- Which columns contain data vs. labels
- Diagram positions relative to table cells

Do NOT start writing HTML until the structure is clear.

**Step 3 — Crop, inspect, and confirm content region by region**

This is the critical step that makes or breaks text accuracy. The ultra-high-res image is too large to read at full size — you must crop it into logical regions (per-column, per-section, or per-row-group) and inspect each crop at native resolution.

- Read the cropped image at 1:1 zoom to confirm every cell's exact text
- Note discrepancies: what looks like one thing at low zoom may differ at full resolution
- Do NOT guess or approximate — if text is ambiguous, re-crop tighter or increase export zoom

```python
from PIL import Image
img = Image.open('page_1.png')
# Crop a specific column region for inspection
col_a1 = img.crop((780, 480, 1400, 1320))
col_a1.save('inspect_A1.jpg', quality=95)
```

Only proceed to Step 4 once you have confirmed the actual text content for every data cell. Building HTML from partial or guessed content leads to silent errors that are hard to catch later.

**Step 4 — Rebuild as static HTML table**

Reconstruct the document as **static HTML only**. Do NOT add JavaScript, CSS hover effects, form inputs, animations, or any interactivity. The goal is visual fidelity, not a web application.

Use `<table>` for tabular layouts. Fixed-width columns (`table-layout: fixed`) prevent stretching. Embed diagrams inside the table as a dedicated `<tr>` so they align exactly with data columns below. Place a blank `<td>` over label columns so diagrams sit only above data.

```html
<tr class="diagram-row">
  <td colspan="2"></td>  <!-- blank over label columns -->
  <td><img src="diagram_A1.jpg"></td>
  <td><img src="diagram_A2.jpg"></td>
</tr>
```

**Step 5 — Precise diagram cropping**

Once table column widths are fixed, go back to the original ultra-high-res image and crop each diagram by exact pixel coordinates. Re-export at tighter bounds if borders or neighboring text leak in.

**Step 6 — Review & Package**

1. Open the HTML in a browser for the user to review
2. Wait for user feedback — fix any issues they point out
3. Once the user is satisfied, **remind them** packaging is available:
   - **Folder**: copy `index.html` + images to a delivery folder
   - **Zip**: run `python pipeline/package_output.py` to create a self-contained zip
4. Let the user choose which format they prefer

## Core Workflow (MinerU-Enhanced)

All documents go through MinerU for content extraction, then Claude for semantic layout and OCR correction.

**Step 0 — MinerU Extraction**

```bash
mineru-open-api extract document.pdf -f html -o mineru_output/ \
  --language cyrillic --model vlm
```

80+ languages supported. For Chinese use `--language ch`, for English `--language en`, etc.

**Step 1 — Parse to Skeleton**

```bash
python pipeline/mineru_parse.py mineru_output/document.html \
  --template templates/cmr/skeleton.json \
  --output partial_skeleton.json
```

If a template exists for the document type (CMR, invoice, etc.), use `--template` to get
accurate field mapping. Otherwise, mineru_parse.py generates a generic skeleton from the
HTML structure — Claude will restructure it in the next step.

**Step 2 — Claude Review & Correct**

Claude reads `partial_skeleton.json` alongside the MinerU HTML output and:
- Fixes OCR errors
- Reassigns text to correct fields
- Adds `pair_id` to left/right sections for 2-column pairing
- Marks full-width sections (`full_width: true`)

**Step 3 — Render HTML**

```bash
python pipeline/render_skeleton.py filled_skeleton.json --output document.html
```

### Fallback: Vision-First (MinerU unavailable)

If mineru-open-api is not installed or the API is unreachable, fall back to Claude Vision:

```
PDF → export_pdf.py → full_page.png → Claude Vision → skeleton.json
  → auto_crop.py → Claude Vision per-crop → filled_skeleton.json
  → render_skeleton.py → document.html
```

### Skeleton-Driven Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `pipeline/mineru_parse.py` | MinerU HTML → skeleton | `python pipeline/mineru_parse.py doc.html --template tmpl.json` |
| `pipeline/render_skeleton.py` | Skeleton → HTML | `python pipeline/render_skeleton.py skeleton.json` |
| `pipeline/export_pdf.py` | PDF → high-res PNG | `python pipeline/export_pdf.py input.pdf [zoom]` |

## Quick Scripts

### One-Click Export

Export all PDF pages to ultra-high-res images:

```bash
python pipeline/export_pdf.py input.pdf [zoom]
```

- Default zoom: 3x (approximately 4K on A3)
- Output: `pdf_pages/page_1.png`, `page_2.png`, ...
- Increase zoom if text is still blurry at 1:1

### Auto Grid Crop

Split an image into regions for inspection:

```bash
python pipeline/auto_crop.py image.png [rows cols]
```

- Default grid: 2x2 (4 regions)
- Output: `crops/image_r1c1.jpg`, `r1c2.jpg`, ...
- Generates `image_grid.jpg` with red grid overlay

### Package Output

Bundle reconstructed HTML + images into a deliverable zip:

```bash
python pipeline/package_output.py [output_dir] [zip_name]
```

- Default: current directory, output.zip
- Auto-discovers `page_*.html` files and their referenced images
- Includes `pdf_pages/` originals for reference

## Directory Structure

Follow this convention for all scan-to-html projects:

```
scan-to-html/
├── CLAUDE.md               # Agent auto-discovery entry
├── SKILL.md                # Skill documentation
├── README.md               # User-facing docs
├── pipeline/               # Processing scripts
│   ├── export_pdf.py       # PDF → high-res PNG
│   ├── auto_crop.py        # Auto grid crop
│   ├── mineru_parse.py     # MinerU HTML → skeleton
│   ├── render_skeleton.py  # Skeleton → HTML
│   ├── list_templates.py   # Template discovery
│   ├── generate_previews.py# Preview generation
│   ├── package_output.py   # Output packaging
│   └── skeleton_schema.json# Skeleton JSON schema
├── templates/              # 18 document templates
│   ├── index.html          # Visual template browser
│   └── [category]/         # template.html + preview.png
└── (working files created during processing)
    ├── pdf_pages/          # Ultra-high-res exports
    ├── crops/              # Auto-cropped regions
    └── diagrams/           # Precisely cropped diagrams
```

## Template Library

Pre-built templates for common document types are available in `templates/`.

**Available categories (18 templates):**
- **身份证件**: Passport, ID Card, Driver License, Business Card
- **旅行**: Visa, Boarding Pass, Hotel Booking
- **商务**: Invoice, Receipt, Quotation
- **财务**: Payslip, Bank Statement
- **证书**: Birth Certificate, Diploma, Transcript, Police Clearance
- **法律**: Power of Attorney, Contract

**Discovering templates:**

```bash
python pipeline/list_templates.py              # List all templates
python pipeline/list_templates.py --json       # JSON output for programmatic use
python pipeline/list_templates.py --search 护照  # Search by keyword
python pipeline/list_templates.py --detail passport  # Show placeholders
```

**Usage flow:**
1. Run `python pipeline/list_templates.py` to see available templates
2. Or open `templates/index.html` to browse visually with search/filter
3. Read the template HTML to get placeholder list
4. Fill placeholders with extracted content: `{{SURNAME}}` → `张三`
5. Save as the output HTML file

**To add a new template:**
1. Create directory: `templates/new_type/`
2. Create `template.html` with `{{PLACEHOLDER}}` fields
3. Run `python pipeline/generate_previews.py` to generate preview
4. Add entry to `templates/index.html` grid

## Common Mistakes

| Mistake | Why it fails |
|---------|-------------|
| Export at 1× zoom | Text unreadable; OCR and human review both fail |
| Inspect full image without cropping | Details lost; columns merged; text misread |
| Build HTML before analyzing structure | Column count errors, misaligned diagrams, missing cells |
| Use flexible/percentage widths | Layout drifts; diagrams no longer align with data |
| Skip blank spacer cells for diagram row | Diagrams shift left, no longer above correct columns |
| Add interactivity (JS, hover, forms) | Violates "visual reconstruction" scope; static HTML only |
| Rebuild common document from scratch | Template library likely has it; check first |

## Quick Reference

| Tool | Purpose |
|------|---------|
| PyMuPDF (`fitz`) | PDF → high-res PNG |
| PIL/Pillow | Crop regions, convert formats |
| Browser DevTools | Verify fixed-width table layout |

## Baseline Failures (RED Phase Evidence)

Without this skill, agents typically:
1. Attempt direct PDF text extraction → empty/garbled results
2. Export at default/low resolution → text illegible, forcing guesswork
3. Skip structural analysis → wrong table dimensions, missing data
4. Place diagrams outside the table → misalignment with columns
