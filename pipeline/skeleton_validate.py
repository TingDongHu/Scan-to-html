#!/usr/bin/env python3
"""Validate a skeleton.json file against schema and sanity checks.

Usage: python skeleton_validate.py skeleton.json
Exit code: 0 = valid, 1 = errors found
"""

import sys
import json
import os
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "skeleton_schema.json"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def validate_schema(skeleton, schema):
    import jsonschema
    try:
        jsonschema.validate(skeleton, schema)
        return []
    except jsonschema.ValidationError as e:
        return [str(e)]

def validate_sanity(skeleton):
    errors = []
    pw = skeleton["page"]["width"]
    ph = skeleton["page"]["height"]

    for sec in skeleton.get("sections", []):
        pos = sec["pos"]
        unit = pos.get("unit", "%")

        if unit == "%":
            x = pos["x"] / 100 * pw
            y = pos["y"] / 100 * ph
            w = pos["w"] / 100 * pw
            h = pos["h"] / 100 * ph
        else:
            x, y, w, h = pos["x"], pos["y"], pos["w"], pos["h"]

        if x < 0 or y < 0:
            errors.append(f"Section '{sec['id']}': pos out of bounds (negative)")
        if x + w > pw + 5 or y + h > ph + 5:
            errors.append(f"Section '{sec['id']}': pos exceeds page boundary")

        for field in sec.get("fields", []):
            bx, by, bw, bh = field["bbox"]
            if bw > w or bh > h:
                errors.append(
                    f"Section '{sec['id']}', field '{field['id']}': "
                    f"bbox {field['bbox']} exceeds section size ({w:.0f}x{h:.0f})"
                )

        tbl = sec.get("table")
        if tbl:
            n_headers = len(tbl["headers"])
            for ri, row in enumerate(tbl.get("rows", [])):
                if len(row["cells"]) != n_headers:
                    errors.append(
                        f"Section '{sec['id']}', table row {ri}: "
                        f"{len(row['cells'])} cells vs {n_headers} headers"
                    )

    sections = skeleton.get("sections", [])
    for i in range(len(sections)):
        for j in range(i + 1, len(sections)):
            if sections_overlap(sections[i]["pos"], sections[j]["pos"], pw, ph):
                errors.append(
                    f"Sections '{sections[i]['id']}' and '{sections[j]['id']}' overlap"
                )

    return errors

def sections_overlap(p1, p2, pw, ph):
    def to_px(p):
        u = p.get("unit", "%")
        if u == "%":
            return (p["x"]/100*pw, p["y"]/100*ph,
                    (p["x"]+p["w"])/100*pw, (p["y"]+p["h"])/100*ph)
        return (p["x"], p["y"], p["x"]+p["w"], p["y"]+p["h"])

    a1, b1, a2, b2 = to_px(p1)
    x1, y1, x2, y2 = to_px(p2)
    return not (a2 <= x1 or x2 <= a1 or b2 <= y1 or y2 <= b1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python skeleton_validate.py skeleton.json")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Error: File not found: {path}")
        sys.exit(1)

    skeleton = load_json(path)
    schema = load_json(SCHEMA_PATH)

    schema_errors = validate_schema(skeleton, schema)
    sanity_errors = validate_sanity(skeleton)

    all_errors = schema_errors + sanity_errors

    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        sections = len(skeleton.get("sections", []))
        fields = sum(len(s.get("fields", [])) for s in skeleton.get("sections", []))
        print(f"Skeleton valid: {sections} sections, {fields} fields")
        sys.exit(0)

if __name__ == "__main__":
    main()
