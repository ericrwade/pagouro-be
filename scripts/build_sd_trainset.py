"""Training set for the Belle Époque LoRA (O-37 route B). Needs Pillow (project venv).

Sources: the Met pool rows Jev labelled keep_print / keep_plate (data/images/pool_meta.labelled.jsonl)
and every Library of Congress poster in data/images/loc/ledger.jsonl. Each image: centre square
crop, resized to --size (512 for CommonCanvas-S-C / SD2), saved as PNG under
data/images/sd_train/<size>/ with a caption built from its own metadata:

    "Belle Époque lithograph poster, <title>, by <artist>, <year>"   (LoC / Met poster rows)
    "Victorian trade card lithograph, <title>, <year>"                  (Met trade-card rows)
    "natural history plate engraving of a <subject>, <title>"           (Met plate rows)

A trigger word `belleposter` is prepended to every caption so the LoRA can be addressed.
data/images/sd_train/ledger.jsonl records provenance per row (source, url, licence, sha256 of
the source and of the crop). Nothing from anywhere else goes in.

    .venv/Scripts/python.exe scripts/build_sd_trainset.py --size 512
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "images", "sd_train")
TRIGGER = "belleposter"


def clean(s: str, n: int = 90) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip(" .,;:")
    return s[:n]


def year(s) -> str:
    m = re.search(r"\b(1[5-9]\d{2})\b", str(s or ""))
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--min-contrast", type=float, default=18.0)
    a = ap.parse_args()
    from PIL import Image
    rows = []
    # Met
    lab = {}
    for l in io.open(os.path.join(ROOT, "data", "images", "pool_meta.labelled.jsonl"), encoding="utf-8"):
        if l.strip():
            d = json.loads(l); lab[d["objectID"]] = d.get("style_fit")
    for l in io.open(os.path.join(ROOT, "data", "images", "ledger.jsonl"), encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        fit = lab.get(r["objectID"])
        if fit not in ("keep_print", "keep_plate"):
            continue
        q = (r.get("query") or "").lower()
        title, artist, yr = clean(r.get("title")), clean(r.get("artist"), 40), year(r.get("date"))
        if fit == "keep_plate":
            cap = f"{TRIGGER}, natural history plate engraving, {title}"
        elif "poster" in q or any(k in q for k in ("lautrec", "chéret", "cheret", "mucha", "steinlen", "grasset", "bonnard", "penfield", "rhead", "bradley", "feure", "livemont", "cappiello", "meunier", "orazi", "paleologu", "willette", "lefèvre", "bouisset", "vuillard", "vallotton", "affiche")):
            cap = f"{TRIGGER}, Belle Époque lithograph poster, {title}" + (f", by {artist}" if artist else "") + (f", {yr}" if yr else "")
        elif "trade card" in q or "advertisement" in q or "chromolithograph" in q:
            cap = f"{TRIGGER}, Victorian trade card chromolithograph, {title}" + (f", {yr}" if yr else "")
        else:
            cap = f"{TRIGGER}, {r.get('classification') or 'print'} of the 1880s-1920s, {title}" + (f", {yr}" if yr else "")
        rows.append({"source": "met", "id": str(r["objectID"]), "file": r["file"], "caption": cap, "url": r.get("object_url"),
                     "license": r.get("license"), "sha256_source": r.get("sha256"), "artist": artist, "year": yr, "fit": fit})
    # LoC
    lp = os.path.join(ROOT, "data", "images", "loc", "ledger.jsonl")
    if os.path.exists(lp):
        for l in io.open(lp, encoding="utf-8"):
            if not l.strip():
                continue
            r = json.loads(l)
            contrib = r.get("contributors") or []
            artist = clean(contrib[0] if isinstance(contrib, list) and contrib else contrib, 40) if contrib else ""
            cap = f"{TRIGGER}, Belle Époque lithograph poster, {clean(r.get('title'))}" + (f", by {artist}" if artist else "") + (f", {r.get('end_year')}" if r.get("end_year") else "")
            rows.append({"source": "loc", "id": r["item_url"].rstrip("/").rsplit("/", 1)[-1], "file": r["file"], "caption": cap,
                         "url": r["item_url"], "license": r.get("license"), "sha256_source": r.get("sha256"), "artist": artist,
                         "year": str(r.get("end_year") or ""), "fit": "poster"})
    d = os.path.join(OUT, str(a.size)); os.makedirs(d, exist_ok=True)
    kept, faint = 0, 0
    with io.open(os.path.join(OUT, "ledger.jsonl"), "w", encoding="utf-8", newline="\n") as led, \
         io.open(os.path.join(d, "metadata.jsonl"), "w", encoding="utf-8", newline="\n") as meta:
        for r in rows:
            src = os.path.join(ROOT, r["file"])
            try:
                im = Image.open(src).convert("RGB")
            except Exception:
                continue
            w, h = im.size; side = min(w, h)
            box = ((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side)
            sq = im.crop(box).resize((a.size, a.size), Image.LANCZOS)
            g = sq.convert("L"); ext = g.getextrema()
            px = list(g.getdata()); mean = sum(px) / len(px); std = (sum((v - mean) ** 2 for v in px) / len(px)) ** 0.5
            if std < a.min_contrast:
                faint += 1; continue
            name = f"{r['source']}_{r['id']}.png"
            p = os.path.join(d, name); sq.save(p, "PNG", optimize=True)
            r2 = dict(r); r2["crop_box"] = box; r2["file_train"] = os.path.relpath(p, ROOT).replace("\\", "/")
            r2["sha256_train"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
            led.write(json.dumps(r2, ensure_ascii=False) + "\n")
            meta.write(json.dumps({"file_name": name, "text": r["caption"]}, ensure_ascii=False) + "\n")
            kept += 1
    from collections import Counter
    print(f"rows {len(rows)} -> kept {kept} (faint dropped {faint}); by source {dict(Counter(r['source'] for r in rows))}; -> {os.path.relpath(d, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
