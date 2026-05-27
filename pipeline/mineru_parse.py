#!/usr/bin/env python3
"""Parse MinerU HTML output into a partial skeleton JSON.

Usage:
  python mineru_parse.py mineru_output/document.html --output partial.json
  python mineru_parse.py mineru_output/document.html --template templates/cmr/skeleton.json --output partial.json

Reads MinerU-generated HTML (VLM model, cyrillic language) and maps extracted text
into the skeleton format. When a template skeleton is provided, uses its section
structure and fills field values from MinerU text. Otherwise, generates a generic
skeleton with sequential sections.
"""

import sys
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path


class MinerUHTMLParser(HTMLParser):
    """Extract table rows and cells from MinerU HTML output."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._current_row = []
        self._current_cell = []
        self._in_td = False
        self._in_tr = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._in_tr = True
            self._current_row = []
        elif tag == "td" or tag == "th":
            self._in_td = True
            self._current_cell = []

    def handle_endtag(self, tag):
        if tag == "td" or tag == "th":
            self._in_td = False
            self._current_row.append("".join(self._current_cell).strip())
        elif tag == "tr":
            self._in_tr = False
            if self._current_row:
                self.rows.append(self._current_row)

    def handle_data(self, data):
        if self._in_td:
            self._current_cell.append(data)


def parse_mineru_html(html_path):
    """Parse MinerU HTML file and return list of cell text rows."""
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    parser = MinerUHTMLParser()
    parser.feed(html)
    return parser.rows


def strip_label_prefix(text):
    """Remove leading CMR section number and label keywords from text."""
    # Remove leading number + label pattern like "1Отправитель (наименование..."
    text = re.sub(r'^\d{1,2}\s*[А-ЯA-Z][а-яa-zА-ЯA-Z\s./()«»,\-]+', '', text).strip()
    return text


def match_section_label(cell_text):
    """Try to match a cell's text to a CMR section. Returns (section_id, cleaned_text) or None."""
    patterns = [
        # Left column sections
        (r'1\s*Отправител', 'sender'),
        (r'2\s*Получател', 'recipient'),
        (r'3\s*Место\s*разгрузк', 'carrier_subsequent'),
        (r'4\s*Место\s*и\s*дат[аы]\s*п[оа]гру', 'right_middle'),
        (r'5\s*Прилагаем', 'right_middle'),
        (r'6\s*Зна[кн]и\s*и\s*номер', 'goods_table'),
        (r'13\s*Указани[яй]\s*отправител', 'sender_instructions'),
        (r'14\s*Возврат|14\s*Rücker', 'return_section'),
        (r'15\s*Услови[яй]\s*оплат', 'payment_terms'),
        # Right column sections
        (r'16\s*Перево[зт]', 'carrier_main'),
        (r'17\s*Последующ', 'subsequent_carrier'),
        (r'18\s*Оговорк', 'carrier_notes_payment'),
        (r'19\s*Подлежит\s*оплат|19\s*Zu\s*zahlen', 'carrier_notes_payment'),
        (r'20\s*Особы[её]\s*согласован', 'special_agreements'),
        (r'21\s*Составлен[ао]|21\s*Ausgefertigt', 'signatures'),
        (r'25\s*Регистрац|25\s*Amtl\.\s*Kennz', 'vehicle_info'),
        # CMR header / note section
        (r'Международная\s*товар[но]о\s*-\s*транспортн', 'right_header'),
        # Supplementary goods content (container, dangerous goods)
        (r'Контейнер\s*[N№]', 'goods_table'),
        (r'Класс\s*опасност', 'goods_table'),
    ]
    for pattern, section_id in patterns:
        if re.search(pattern, cell_text, re.IGNORECASE):
            return section_id
    return None


def find_section_boundaries(rows):
    """Identify which rows start new sections and which rows are content."""
    boundaries = []  # list of (row_index, section_id, column: 'left'|'right'|'full')
    for i, cells in enumerate(rows):
        for ci, cell_text in enumerate(cells):
            if not cell_text:
                continue
            sec_id = match_section_label(cell_text)
            if sec_id:
                col = "left" if ci == 0 else "right"
                boundaries.append((i, sec_id, col))
    return boundaries


def group_content_rows(rows, boundaries):
    """Group rows between section boundaries into section content blocks."""
    if not boundaries:
        return []

    groups = []
    for bi in range(len(boundaries)):
        start_idx = boundaries[bi][0]
        sec_id = boundaries[bi][1]
        col = boundaries[bi][2]
        end_idx = boundaries[bi + 1][0] if bi + 1 < len(boundaries) else len(rows)

        # Collect content: rows from start_idx to end_idx-1, only the relevant column
        content_lines = []
        for ri in range(start_idx, end_idx):
            cells = rows[ri]
            if col == "left" and len(cells) >= 1:
                text = cells[0]
            elif col == "right" and len(cells) >= 2:
                text = cells[1]
            elif len(cells) >= 1:
                text = cells[0]
            else:
                continue

            # Clean up label prefix from first row
            if ri == start_idx:
                text = strip_label_prefix(text)
            if text:
                content_lines.append(text)

        groups.append({
            "section_id": sec_id,
            "column": col,
            "text": "\n".join(content_lines),
        })

    return groups


def parse_goods_table(rows, boundary_idx, boundaries):
    """Extract goods table data from MinerU rows."""
    # Find the goods table boundary
    goods_start = None
    for bi, b in enumerate(boundaries):
        if b[1] == "goods_table" and bi == boundary_idx:
            goods_start = b[0]
            break
    if goods_start is None:
        return {}

    end_idx = boundaries[boundary_idx + 1][0] if boundary_idx + 1 < len(boundaries) else len(rows)

    # Look for goods name, HS code, container, weight, volume
    result = {
        "goods_name": "",
        "hs_code": "",
        "gross_weight": "",
        "volume": "",
        "container": "",
        "seal": "",
        "danger_class": "",
        "un_code": "",
    }

    for ri in range(goods_start, end_idx):
        cells = rows[ri]
        # Check ALL cells in the row (MinerU may split content across colspan cells)
        combined = " ".join(c for c in cells if c)

        # Match goods name (Cyrillic + liquid helium) — prefer first cell with it
        for cell_text in cells:
            if re.search(r'Гели[йя]\s*жидк', cell_text):
                result["goods_name"] = cell_text.strip()
                break

        # Match HS code (8-10 digit number starting with 28)
        if re.search(r'\b2804\w{6}\b', combined):
            result["hs_code"] = re.search(r'\b(2804\w{6})\b', combined).group(1)

        # Match container number
        container_match = re.search(r'[A-Z]{4}(\d{7})', combined)
        if container_match:
            result["container"] = container_match.group(0)

        # Match gross weight and volume (they appear together)
        wt_vol = re.search(r'(\d[\d\s,]+)\s*кг.*?(\d[\d\s,]+)\s*м[3³]', combined)
        if wt_vol:
            result["gross_weight"] = wt_vol.group(1).strip()
            result["volume"] = wt_vol.group(2).strip()

        # Match danger class
        dc = re.search(r'Класс\s*опасности:\s*([\d.]+)', combined)
        if dc:
            result["danger_class"] = dc.group(1)

        # Match UN code
        un = re.search(r'UN\s*(\d{4})', combined)
        if un:
            result["un_code"] = "UN " + un.group(1)

    return result


def fill_field_values(skeleton, content_groups, goods_data):
    """Fill skeleton field values from MinerU content groups."""
    # Build lookup from section_id to content text
    content_map = {}
    for group in content_groups:
        sid = group["section_id"]
        # If duplicate section_id (e.g., goods_table appears multiple times), append
        if sid in content_map:
            content_map[sid] += "\n" + group["text"]
        else:
            content_map[sid] = group["text"]

    for section in skeleton["sections"]:
        sid = section["id"]
        text = content_map.get(sid, "")

        # Special handling for goods_table
        if sid == "goods_table" and goods_data:
            # Fill goods table
            tbl = section.get("table")
            if tbl and tbl.get("rows"):
                row0 = tbl["rows"][0]["cells"]
                for cell in row0:
                    if cell.get("value", "") == "" and not cell.get("value"):
                        pass  # Keep empty
                # Fill data row cells
                row0[0]["value"] = goods_data.get("goods_name", "")
                row0[4]["value"] = goods_data.get("hs_code", "")
                row0[5]["value"] = goods_data.get("gross_weight", "")
                row0[6]["value"] = goods_data.get("volume", "")

            # Fill supplementary fields
            for field in section.get("fields", []):
                fid = field["id"]
                if fid == "container_info":
                    ctr = goods_data.get("container", "")
                    field["value"] = f"Контейнер № {ctr}\nПломба №" if ctr else ""
                elif fid == "dangerous_goods":
                    dc = goods_data.get("danger_class", "")
                    un = goods_data.get("un_code", "")
                    if dc or un:
                        field["value"] = f"Класс опасности: {dc}\nкод: {un}\nДОПОГ: ADR"
                elif fid == "total_gross":
                    field["value"] = goods_data.get("gross_weight", "")
                elif fid == "total_volume":
                    field["value"] = goods_data.get("volume", "")

        # Fill regular sections: distribute text across non-goods fields
        elif text:
            fields = section.get("fields", [])
            # Skip if this section has a table (handled separately)
            if section.get("table"):
                continue

            # Put all text into first field if only one, else split by newlines
            if fields:
                lines = text.split("\n")
                for fi, field in enumerate(fields):
                    if field["id"] in ("total_gross", "total_volume", "container_info", "dangerous_goods"):
                        continue  # Skip goods_table fields
                    if fi < len(lines):
                        field["value"] = lines[fi]
                    else:
                        break

    return skeleton


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    args = sys.argv[1:]
    html_path = None
    template_path = None
    output_path = "partial_skeleton.json"

    i = 0
    while i < len(args):
        if args[i] == "--template" and i + 1 < len(args):
            template_path = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif not html_path and not args[i].startswith("--"):
            html_path = args[i]
            i += 1
        else:
            i += 1

    if not html_path:
        print("Usage: python mineru_parse.py mineru_output/doc.html [--template skeleton.json] [--output partial.json]")
        sys.exit(1)

    if not os.path.exists(html_path):
        print(f"Error: HTML file not found: {html_path}")
        sys.exit(1)

    print(f"Parsing MinerU HTML: {html_path}")
    rows = parse_mineru_html(html_path)
    print(f"  Found {len(rows)} table rows")

    # Load or create skeleton
    if template_path and os.path.exists(template_path):
        print(f"Using template: {template_path}")
        skeleton = load_json(template_path)
    else:
        # Generic skeleton fallback
        print("No template provided, generating generic skeleton")
        skeleton = {
            "doc": "unknown",
            "page": {"width": 1786, "height": 2526},
            "sections": [],
        }

    # Find section boundaries in MinerU output
    boundaries = find_section_boundaries(rows)
    print(f"  Found {len(boundaries)} section boundaries")

    # Group content rows into sections
    content_groups = group_content_rows(rows, boundaries)

    # Parse goods table data (accumulate across all goods_table boundaries)
    goods_data = {}
    for bi, b in enumerate(boundaries):
        if b[1] == "goods_table":
            partial = parse_goods_table(rows, bi, boundaries)
            # Merge: only overwrite if current value is empty
            for k, v in partial.items():
                if v and not goods_data.get(k):
                    goods_data[k] = v
    if goods_data:
        print(f"  Goods table: {goods_data.get('goods_name', 'N/A')} "
              f"{goods_data.get('gross_weight', '')}kg {goods_data.get('volume', '')}m3")

    # Fill field values
    skeleton = fill_field_values(skeleton, content_groups, goods_data)

    save_json(skeleton, output_path)
    print(f"Partial skeleton saved: {output_path}")
    print(f"  {len(skeleton['sections'])} sections, "
          f"{sum(len(s.get('fields', [])) for s in skeleton['sections'])} fields")


if __name__ == "__main__":
    main()
