"""Draw 1.0: the pool is not the training set (D-67). Select from data/images/ledger.jsonl, downsample,
and write data/images/train/ with its own ledger.

Selection (all three must hold, or the row is a plate exception):
  * classification in PRINT_KINDS (prints, drawings, paintings, books, posters, ...)
  * end_year >= --min-year (1850: the print world O-28 names; the Met's 'shell' hits from
    antiquity go out)
  * image at least 200 px on the short side (already true of the pool)
  Plate exception: a row whose title or tags mention a shell / crab / mollusc / nautilus subject is
  kept at any date if it is a print or drawing (naturalist plates are the hermit crab's ancestry).

Each kept image: centre square crop, Lanczos downsample to 64x64 and 32x32, saved as PNG (RGB, no
palette - quantisation is a training-time step against app/palettes.py once HOUSE is chosen).
The training ledger repeats the pool row's provenance fields and adds the crop box and both hashes.

    .venv/Scripts/python.exe scripts/curate_draw_corpus.py [--min-year 1850]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "data", "images", "ledger.jsonl")
OUT = os.path.join(ROOT, "data", "images", "train")

PRINT_KINDS = {"prints", "drawings", "paintings", "books", "posters", "prints|ephemera", "ephemera",
               "albums", "photographs", "illustrated books", "periodicals", "trade cards", "ornament prints"}
SUBJECT = re.compile(r"\b(shell|shells|seashell|crab|crabs|hermit|mollus|nautilus|conch|crustacea|snail)\b", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-year", type=int, default=1850)
    ap.add_argument("--sizes", nargs="*", type=int, default=[64, 32])
    ap.add_argument("--min-contrast", type=float, default=22.0, help="luminance std-dev floor at 64 px")
    ap.add_argument("--jev-labels", help="pool_meta.labelled.jsonl from jev_label.py (O-36 use #3): select rows whose style_fit is keep_print / keep_plate instead of the keyword rules")
    a = ap.parse_args()
    jev = {}
    if a.jev_labels:
        for l in io.open(a.jev_labels, encoding="utf-8"):
            if l.strip():
                d = json.loads(l); jev[d["objectID"]] = d.get("style_fit")
    from PIL import Image
    rows = [json.loads(l) for l in io.open(POOL, encoding="utf-8") if l.strip()]
    kept, why = [], {"print_world": 0, "plate_exception": 0, "dropped_kind": 0, "dropped_year": 0, "dropped_faint": 0}
    for r in rows:
        kind = (r.get("classification") or "").lower()
        is_print = any(k in kind for k in PRINT_KINDS)          # an empty classification is not a print
        subject = bool(SUBJECT.search((r.get("title") or "") + " " + " ".join(r.get("tags") or [])))
        if jev:
            lab = jev.get(r["objectID"])
            if lab == "keep_print":
                why["print_world"] += 1; kept.append(r)
            elif lab == "keep_plate":
                why["plate_exception"] += 1; kept.append(r)
            else:
                why["dropped_kind"] += 1
            continue
        if is_print and (r.get("end_year") or 0) >= a.min_year:
            why["print_world"] += 1; kept.append(r)
        elif is_print and subject:
            why["plate_exception"] += 1; kept.append(r)
        elif not is_print:
            why["dropped_kind"] += 1
        else:
            why["dropped_year"] += 1
    for s in a.sizes:
        os.makedirs(os.path.join(OUT, str(s)), exist_ok=True)
    led_path = os.path.join(OUT, "ledger.jsonl")
    n = 0
    with io.open(led_path, "w", encoding="utf-8", newline="\n") as led:
        for r in kept:
            src = os.path.join(ROOT, r["file"])
            try:
                im = Image.open(src).convert("RGB")
            except Exception:
                continue
            w, h = im.size
            side = min(w, h)
            box = ((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side)
            sq = im.crop(box)
            # contrast floor: a faint pencil study is a blank square at 64 px (luminance std-dev on the 64 px version)
            probe = sq.resize((64, 64), Image.LANCZOS).convert("L")
            px = list(probe.getdata()); mean = sum(px) / len(px)
            std = (sum((v - mean) ** 2 for v in px) / len(px)) ** 0.5
            if std < a.min_contrast:
                why["dropped_faint"] += 1
                continue
            out_row = {k: r[k] for k in ("objectID", "title", "artist", "date", "end_year", "medium", "classification",
                                         "tags", "object_url", "image_url", "license", "sha256", "file") if k in r}
            out_row["crop_box"] = box
            if jev:
                out_row["selected_by"] = f"jev style_fit={jev.get(r['objectID'])} (O-36 use #3, jev-1.13.0, 2026-09-20) + contrast floor"
            for s in a.sizes:
                small = sq.resize((s, s), Image.LANCZOS)
                p = os.path.join(OUT, str(s), f"{r['objectID']}.png")
                small.save(p, "PNG", optimize=True)
                out_row[f"file_{s}"] = os.path.relpath(p, ROOT).replace("\\", "/")
                out_row[f"sha256_{s}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
            led.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            n += 1
    print(f"pool {len(rows):,} -> kept {n:,} ({why}); sizes {a.sizes}; ledger {os.path.relpath(led_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
