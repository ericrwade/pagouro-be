"""Pagouro BE Styles training sets. For each style in styles.json: read every source ledger under
data/images/styles/<folder>/ with its Qwen captions, crop the image to the captioner's artwork box
(mount, ruler and colour strip removed), then take the centre square at --size and, for a tall or wide
artwork, a second square at the other end. Caption: "<trigger>, <phrase>, <content caption>".
Writes data/images/styles_train/<style>/512/{*.png, metadata.jsonl} and a ledger with provenance,
crop boxes, the caption as trained and the SHA-256 of each training file.

    python scripts/build_style_trainset.py --styles rockart ukiyoe [--size 512] [--max-per-style 1500]
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BE = os.path.dirname(HERE)
DATA = os.path.abspath(os.environ.get("PAGOURO_DATA") or os.path.join(BE, "..", "PAGOURO_BUILD", "data", "images"))


def clean(s, n=200):
    return re.sub(r"\s+", " ", str(s or "")).strip(" .,;:")[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--styles", nargs="+", required=True)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--min-contrast", type=float, default=14.0)
    ap.add_argument("--max-per-style", type=int, default=1500)
    ap.add_argument("--require-caption", action="store_true", default=True)
    a = ap.parse_args()
    from PIL import Image
    styles = json.load(io.open(os.path.join(BE, "styles.json"), encoding="utf-8"))
    for st in a.styles:
        cfg = styles[st]
        rows = []
        for folder in cfg["folders"]:
            lp = os.path.join(DATA, "styles", folder, "ledger.jsonl")
            if not os.path.exists(lp):
                print("no ledger for", folder); continue
            caps = {}
            cp = lp + ".captions.jsonl"
            if os.path.exists(cp):
                for l in io.open(cp, encoding="utf-8"):
                    c = json.loads(l); caps[c["id"]] = c
            for l in io.open(lp, encoding="utf-8"):
                r = json.loads(l); c = caps.get(r["id"])
                if not c: continue
                rows.append((r, c, os.path.join(DATA, "styles", folder, r["file"])))
        rows = rows[:a.max_per_style]
        out = os.path.join(DATA, "styles_train", st); d = os.path.join(out, str(a.size)); os.makedirs(d, exist_ok=True)
        kept = faint = bad = 0; seen = set()
        with io.open(os.path.join(out, "ledger.jsonl"), "w", encoding="utf-8", newline="\n") as led, \
             io.open(os.path.join(d, "metadata.jsonl"), "w", encoding="utf-8", newline="\n") as meta:
            for r, c, src in rows:
                if r.get("sha256") in seen: continue
                seen.add(r.get("sha256"))
                try:
                    im = Image.open(src).convert("RGB")
                except Exception:
                    bad += 1; continue
                W, H = im.size; bx = c.get("artwork_box") or [0, 0, 1, 1]
                x0, y0, x1, y1 = int(bx[0] * W), int(bx[1] * H), int(bx[2] * W), int(bx[3] * H)
                if x1 - x0 >= 128 and y1 - y0 >= 128:
                    im = im.crop((x0, y0, x1, y1))
                w, h = im.size; side = min(w, h)
                crops = [("c", ((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))]
                if h / w >= 1.3: crops.append(("t", ((w - side) // 2, 0, (w - side) // 2 + side, side)))
                elif w / h >= 1.3: crops.append(("l", (0, (h - side) // 2, side, (h - side) // 2 + side)))
                cap = f"{cfg['trigger']}, {cfg['phrase']}, {clean(c['caption_content'])}"
                for tag, box in crops:
                    sq = im.crop(box).resize((a.size, a.size), Image.LANCZOS)
                    g = sq.convert("L"); px = list(g.getdata()); mean = sum(px) / len(px)
                    std = (sum((v - mean) ** 2 for v in px) / len(px)) ** 0.5
                    if std < a.min_contrast: faint += 1; continue
                    name = f"{r['id']}_{tag}.png"; p = os.path.join(d, name); sq.save(p, "PNG", optimize=True)
                    led.write(json.dumps({**{k: v for k, v in r.items()}, "artwork_box": bx, "crop": tag, "crop_box": box, "caption": cap,
                                          "caption_source": c.get("caption_source"), "file_train": f"{st}/{a.size}/{name}",
                                          "sha256_train": hashlib.sha256(open(p, "rb").read()).hexdigest()}, ensure_ascii=False) + "\n")
                    meta.write(json.dumps({"file_name": name, "text": cap}, ensure_ascii=False) + "\n"); kept += 1
        src_counts = Counter(r["source"] for r, _, _ in rows)
        print(f"{st}: {len(rows)} images ({dict(src_counts)}) -> {kept} training files; faint {faint}, unreadable {bad}; -> {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
