"""Pagouro BE training set (D-98). Needs Pillow (the Pagouro venv).

Sources, each with its own ledger and licence per row:
  - Met Open Access (CC0): the rows already curated for D-75 (data/images/sd_train/ledger.jsonl, source "met")
  - Library of Congress Artist Posters (no known restrictions): data/images/loc/ledger.jsonl
  - Art Institute of Chicago (CC0, is_public_domain): data/images/aic/ledger.jsonl
Content captions (machine-written, labelled) come from <ledger>.captions.jsonl beside each ledger.

Caption assembled per image:
  "belleposter, Belle Époque lithograph poster, <content caption>, by <artist>, <year>"
The content caption is the one the model must learn to follow; artist and year are kept because
they carry style signal and are the object's own record.

Crops: every image gives its centre square at --size; a tall image (h/w >= 1.3) also gives its top
square (where the lettering usually is), captioned the same. Faint scans (std < --min-contrast)
are dropped. Output: data/images/be_train/<size>/{*.png, metadata.jsonl} and
data/images/be_train/ledger.jsonl with provenance per training file.

    python scripts/build_be_trainset.py --size 512
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.environ.get("PAGOURO_DATA") or os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", "data", "images"))
BUILD_ROOT = os.path.abspath(os.path.join(DATA, "..", ".."))   # PAGOURO_BUILD (Met/LoC ledgers hold paths relative to it)
OUT = os.path.join(DATA, "be_train")
TRIGGER = "belleposter"


def clean(s, n=90):
    s = re.sub(r"\s+", " ", str(s or "")).strip(" .,;:")
    return s[:n]


def year(s):
    m = re.search(r"\b(1[5-9]\d{2})\b", str(s or ""))
    return m.group(1) if m else ""


def load_captions(ledger_path):
    p = ledger_path + ".captions.jsonl"
    caps = {}
    if os.path.exists(p):
        for l in io.open(p, encoding="utf-8"):
            r = json.loads(l)
            caps[r["id"]] = (r["caption_content"], r["caption_source"])
    return caps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--min-contrast", type=float, default=18.0)
    ap.add_argument("--tall", type=float, default=1.3)
    ap.add_argument("--require-caption", action="store_true", help="drop rows without a content caption")
    a = ap.parse_args()
    from PIL import Image

    rows = []
    # Met: reuse the D-75 curation (rows with source met in the old sd_train ledger point at the source files)
    old = os.path.join(DATA, "sd_train", "ledger.jsonl")
    met_caps = load_captions(os.path.join(DATA, "met_curated.jsonl"))
    if os.path.exists(old):
        for l in io.open(old, encoding="utf-8"):
            r = json.loads(l)
            if r.get("source") != "met":
                continue
            cc = met_caps.get(r["id"]) or met_caps.get(f"met_{r['id']}")
            rows.append({"source": "met", "id": f"met_{r['id']}", "src": os.path.join(BUILD_ROOT, r["file"]),
                         "artist": r.get("artist") or "", "year": r.get("year") or "", "title": "",
                         "url": r.get("url"), "license": r.get("license"), "sha256_source": r.get("sha256_source"),
                         "content": cc[0] if cc else "", "caption_source": cc[1] if cc else ""})
    # LoC
    lp = os.path.join(DATA, "loc", "ledger.jsonl")
    caps = load_captions(lp)
    for l in io.open(lp, encoding="utf-8"):
        r = json.loads(l)
        rid = r["item_url"].rstrip("/").rsplit("/", 1)[-1]
        contrib = r.get("contributors") or []
        artist = clean(contrib[0] if isinstance(contrib, list) and contrib else contrib, 40) if contrib else ""
        cc = caps.get(rid) or caps.get(r.get("id", ""))
        rows.append({"source": "loc", "id": f"loc_{rid}", "src": os.path.join(BUILD_ROOT, r["file"]),
                     "artist": artist, "year": str(r.get("end_year") or year(r.get("date")) or ""), "title": clean(r.get("title")),
                     "url": r["item_url"], "license": r.get("license"), "sha256_source": r.get("sha256"),
                     "content": cc[0] if cc else "", "caption_source": cc[1] if cc else ""})
    # AIC
    apth = os.path.join(DATA, "aic", "ledger.jsonl")
    if os.path.exists(apth):
        caps = load_captions(apth)
        for l in io.open(apth, encoding="utf-8"):
            r = json.loads(l)
            cc = caps.get(r["id"])
            rows.append({"source": "aic", "id": r["id"], "src": os.path.join(DATA, "aic", r["file"]),
                         "artist": clean(r.get("artist"), 40), "year": str(r.get("year") or ""), "title": clean(r.get("title")),
                         "url": r["item_url"], "license": r.get("license"), "sha256_source": r.get("sha256"),
                         "content": cc[0] if cc else "", "caption_source": cc[1] if cc else ""})

    d = os.path.join(OUT, str(a.size))
    os.makedirs(d, exist_ok=True)
    kept = faint = missing = nocap = 0
    seen_sha = set()
    with io.open(os.path.join(OUT, "ledger.jsonl"), "w", encoding="utf-8", newline="\n") as led, \
         io.open(os.path.join(d, "metadata.jsonl"), "w", encoding="utf-8", newline="\n") as meta:
        for r in rows:
            if a.require_caption and not r["content"]:
                nocap += 1
                continue
            if r.get("sha256_source") in seen_sha:
                continue
            seen_sha.add(r.get("sha256_source"))
            try:
                im = Image.open(r["src"]).convert("RGB")
            except Exception:  # noqa: BLE001
                missing += 1
                continue
            w, h = im.size
            side = min(w, h)
            crops = [("c", ((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))]
            if h / w >= a.tall:
                crops.append(("t", ((w - side) // 2, 0, (w - side) // 2 + side, side)))
            body = r["content"] or r["title"]
            cap = f"{TRIGGER}, Belle Époque lithograph poster, {clean(body, 200)}" + (f", by {r['artist']}" if r["artist"] else "") + (f", {r['year']}" if r["year"] else "")
            for tag, box in crops:
                sq = im.crop(box).resize((a.size, a.size), Image.LANCZOS)
                g = sq.convert("L")
                px = list(g.getdata())
                mean = sum(px) / len(px)
                std = (sum((v - mean) ** 2 for v in px) / len(px)) ** 0.5
                if std < a.min_contrast:
                    faint += 1
                    continue
                name = f"{r['id']}_{tag}.png"
                p = os.path.join(d, name)
                sq.save(p, "PNG", optimize=True)
                led.write(json.dumps({**{k: v for k, v in r.items() if k != "src"}, "crop": tag, "crop_box": box, "caption": cap,
                                      "file_train": os.path.relpath(p, DATA).replace("\\", "/"),
                                      "sha256_train": hashlib.sha256(open(p, "rb").read()).hexdigest()}, ensure_ascii=False) + "\n")
                meta.write(json.dumps({"file_name": name, "text": cap}, ensure_ascii=False) + "\n")
                kept += 1
    c = Counter(r["source"] for r in rows)
    withcap = sum(1 for r in rows if r["content"])
    print(f"rows {len(rows)} ({dict(c)}; with content caption {withcap}) -> training files {kept}; faint {faint}, missing {missing}, no caption {nocap}; -> {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
