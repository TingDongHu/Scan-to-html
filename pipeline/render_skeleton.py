#!/usr/bin/env python3
"""Render a filled skeleton.json to static HTML.

Usage: python render_skeleton.py skeleton.json [--output output.html]

Reads a skeleton with filled field values and generates a static HTML
table-based layout matching the original document structure.
"""

import sys
import json
import os

STYLE = """
body { font-family: "Times New Roman", Times, serif; font-size: 10pt; padding: 20px; background: #fff; }
h1 { font-size: 14pt; text-align: center; margin-bottom: 4px; }
table { width: 100%; border-collapse: collapse; margin: 0; }
td, th { border: 1px solid #000; padding: 4px 6px; vertical-align: top; font-size: 9pt; }
th { background: #e8e8e8; font-weight: bold; text-align: center; }
.label { color: #555; font-size: 7pt; }
.val { font-weight: bold; }
.center { text-align: center; }
.bold { font-weight: bold; }
.italic { font-style: italic; }
"""

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def style_class(styles):
    if not styles:
        return ""
    return " " + " ".join(styles)

def render_field(field):
    styles = field.get("style", [])
    cls = style_class(styles)
    return f'<span class="val{cls}">{field.get("value", "")}</span>'

def render_section(sec):
    """Render a single section as one cell in a table row."""
    html = []
    label = sec.get("label", "")
    if label:
        html.append(f'<span class="sec">{label}</span>')

    for field in sec.get("fields", []):
        html.append(render_field(field))

    tbl = sec.get("table")
    if tbl:
        html.append('<table>')
        html.append('<tr>')
        for h in tbl["headers"]:
            html.append(f'<th>{h}</th>')
        html.append('</tr>')
        for row in tbl.get("rows", []):
            html.append('<tr>')
            for cell in row.get("cells", []):
                cs = cell.get("colspan", 1)
                s = style_class(cell.get("style", []))
                colspan = f' colspan="{cs}"' if cs > 1 else ""
                styles = cell.get("style", [])
                all_classes = ["center"] + styles
                classes = " ".join(sorted(set(c for c in all_classes if c)))
                cls_str = f' class="{classes}"' if classes else ""
                html.append(f'<td{cls_str}{colspan}>{cell.get("value", "")}</td>')
            html.append('</tr>')
        html.append('</table>')

    return "\n".join(html)

def section_y_mid(sec):
    """Return the vertical midpoint of a section as percentage."""
    return sec["pos"]["y"] + sec["pos"]["h"] / 2

def sections_overlap_y(sec_a, sec_b):
    """Check if two sections overlap vertically (share ≥30% of their combined height range)."""
    a_top = sec_a["pos"]["y"]
    a_bot = a_top + sec_a["pos"]["h"]
    b_top = sec_b["pos"]["y"]
    b_bot = b_top + sec_b["pos"]["h"]

    overlap_top = max(a_top, b_top)
    overlap_bot = min(a_bot, b_bot)
    overlap_h = max(0, overlap_bot - overlap_top)

    min_h = min(sec_a["pos"]["h"], sec_b["pos"]["h"])
    return overlap_h > min_h * 0.3

def pair_sections(sections):
    """Pair sections for 2-column layout. Returns list of (left, right) tuples.

    Priority: 1) pair_id, 2) y-overlap matching, 3) index-based fallback.
    Full-width sections are returned as single-item pairs.
    """
    # Separate full-width sections first
    full = [s for s in sections if s.get("full_width")]
    normal = [s for s in sections if not s.get("full_width")]

    # Group by explicit pair_id
    paired_by_id = {}
    unpaired = []
    for sec in normal:
        pid = sec.get("pair_id")
        if pid:
            paired_by_id.setdefault(pid, []).append(sec)
        else:
            unpaired.append(sec)

    pairs = []

    # Full-width sections get their own row
    for sec in full:
        pairs.append((sec, None))

    # pair_id groups
    for pid, group in paired_by_id.items():
        left_candidates = [s for s in group if s["pos"]["x"] < 50]
        right_candidates = [s for s in group if s["pos"]["x"] >= 50]
        left_sec = left_candidates[0] if left_candidates else None
        right_sec = right_candidates[0] if right_candidates else None
        pairs.append((left_sec, right_sec))

    # Remaining unpaired: use y-overlap matching
    left_unpaired = [s for s in unpaired if s["pos"]["x"] < 50]
    right_unpaired = [s for s in unpaired if s["pos"]["x"] >= 50]

    used_right = set()
    for lsec in sorted(left_unpaired, key=section_y_mid):
        best_match = None
        best_dist = float("inf")
        for ri, rsec in enumerate(right_unpaired):
            if ri in used_right:
                continue
            if sections_overlap_y(lsec, rsec):
                dist = abs(section_y_mid(lsec) - section_y_mid(rsec))
                if dist < best_dist:
                    best_dist = dist
                    best_match = ri
        if best_match is not None:
            used_right.add(best_match)
            pairs.append((lsec, right_unpaired[best_match]))
        else:
            pairs.append((lsec, None))

    for ri, rsec in enumerate(right_unpaired):
        if ri not in used_right:
            pairs.append((None, rsec))

    return pairs

def render_html(skeleton):
    title = skeleton.get("doc", "Document").upper()
    sections = skeleton.get("sections", [])

    html = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="UTF-8">',
            f'<title>{title}</title>', '<style>', STYLE, '</style>', '</head>', '<body>']

    pairs = pair_sections(sections)

    for left_sec, right_sec in pairs:
        html.append('<table><tr>')

        if left_sec and left_sec.get("full_width"):
            html.append(f'<td colspan="2">{render_section(left_sec)}</td>')
        elif right_sec and right_sec.get("full_width"):
            html.append(f'<td colspan="2">{render_section(right_sec)}</td>')
        else:
            if left_sec:
                html.append(f'<td style="width:50%">{render_section(left_sec)}</td>')
            else:
                html.append('<td style="width:50%"></td>')

            if right_sec:
                html.append(f'<td style="width:50%">{render_section(right_sec)}</td>')
            else:
                html.append('<td style="width:50%"></td>')

        html.append('</tr></table>')

    html.append('</body></html>')
    return "\n".join(html)

def main():
    if len(sys.argv) < 2:
        print("Usage: python render_skeleton.py skeleton.json [--output output.html]")
        sys.exit(1)

    skeleton_path = sys.argv[1]
    output_path = "output.html"

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            i += 1

    if not os.path.exists(skeleton_path):
        print(f"Error: Skeleton not found: {skeleton_path}")
        sys.exit(1)

    skeleton = load_json(skeleton_path)
    html = render_html(skeleton)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    sections = len(skeleton.get("sections", []))
    print(f"Rendered {sections} sections -> {output_path}")

if __name__ == "__main__":
    main()
