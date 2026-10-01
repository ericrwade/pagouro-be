"""Showcase: twelve pictures from the shipped model's own gate run (round 3, plain decode), chosen by hand
from the 160 gate images, each labelled with its caption and seed, plus one honest failure. Writes
showcase/<id>_s<seed>.png (512 px), showcase/sheet.jpg (4x3 contact sheet), showcase/strip.jpg (a wide
strip for the site) and showcase/README.md. Nothing is retouched; these are gate outputs as generated.

    python scripts/make_showcase.py
"""
from __future__ import annotations
import io, json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

BE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(BE, "runs", "round3", "gate", "ft")
OUT = os.path.join(BE, "showcase")
# (id, seed) pairs — the picture the caption asked for, in the style; the last one is the failure kept on purpose
PICKS = [("g09", 0), ("g13", 1), ("g24", 0), ("g17", 2), ("g18", 1), ("g15", 0),
         ("g01", 0), ("g03", 1), ("g21", 2), ("g26", 0), ("g12", 1), ("g27", 0)]


def main():
    os.makedirs(OUT, exist_ok=True)
    gate = {json.loads(l)["id"]: json.loads(l) for l in io.open(os.path.join(BE, "evals", "gate40.jsonl"), encoding="utf-8")}
    meta = {m["file"]: m for m in json.load(open(os.path.join(GATE, "meta.json"), encoding="utf-8"))}
    verdicts = {}
    for l in io.open(os.path.join(BE, "evals", "results", "round3", "verdicts_ft_v2.jsonl"), encoding="utf-8"):
        r = json.loads(l); verdicts[r["file"]] = r
    rows = []
    tiles = []
    for gid, seed in PICKS:
        fn = f"{gid}_s{seed}.png"
        src = os.path.join(GATE, fn)
        shutil.copyfile(src, os.path.join(OUT, fn))
        v = verdicts.get(fn, {})
        rows.append((fn, gate[gid]["caption"], 1000 + seed, v.get("subject"), v.get("unasked_lettering"), v.get("note", "")))
        tiles.append(Image.open(src).convert("RGB"))
    # contact sheet 4 x 3 at 384 px with a caption band
    W, H, band = 384, 384, 44
    sheet = Image.new("RGB", (W * 4, (H + band) * 3), (243, 234, 216))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("georgia.ttf", 15)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
    for i, (im, row) in enumerate(zip(tiles, rows)):
        x, y = (i % 4) * W, (i // 4) * (H + band)
        sheet.paste(im.resize((W, H), Image.LANCZOS), (x, y))
        cap = row[1]
        if len(cap) > 46:
            cap = cap[:44] + "…"
        d.text((x + 8, y + H + 12), cap, fill=(42, 33, 24), font=font)
    sheet.save(os.path.join(OUT, "sheet.jpg"), quality=86)
    strip = Image.new("RGB", (256 * 6, 256), (243, 234, 216))
    for i, im in enumerate(tiles[:6]):
        strip.paste(im.resize((256, 256), Image.LANCZOS), (i * 256, 0))
    strip.save(os.path.join(OUT, "strip.jpg"), quality=84)
    lines = ["# Pagouro BE — showcase", "",
             "Twelve pictures from the shipped model's own gate run (round 3, plain decode, 20 steps, guidance 7, 512 px),",
             "chosen by hand from the 160 gate images and not retouched. Each line gives the caption as asked, the seed,",
             "and the strict judge's two verdicts for that picture: *subject drawn* and *unasked lettering present*. The",
             "last picture is a lettering caption kept on purpose: the asked-for word is not legible, which is what the box says.",
             "", "| picture | caption | seed | subject drawn | unasked lettering | judge's note |", "|---|---|---|---|---|---|"]
    for fn, cap, seed, subj, let, note in rows:
        lines.append(f"| `{fn}` | {cap} | {seed} | {'yes' if subj else 'no'} | {'yes' if let else 'no'} | {note[:90]} |")
    lines += ["", "![sheet](sheet.jpg)", "", "Outputs are CC0. Reproduce any of them with the model file and `sd-cli` using the caption as",
              "`belleposter, Belle Epoque lithograph poster, <caption>` and the seed shown (`-s`)."]
    io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("showcase:", len(rows), "pictures;", sum(1 for r in rows if r[3]), "subject yes;", sum(1 for r in rows if r[4]), "unasked lettering yes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
