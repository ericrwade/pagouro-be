"""Jigsaw batch 2: contact sheets for the eye check of the judge's clean picks.

Clean = subject seen, faces not bad, no lettering, poster style (same filter as batch 1). Writes
showcase/jigsaw_b2/sheets/sheet_NN.jpg (30 per sheet, 6 x 5 at 256 px, each labelled with its caption number) and
faces_NN.jpg (every pick whose caption has people, 4 per sheet at 512 px, the full original).

    python scripts/showcase_jigsaw_b2_sheets.py
"""
import io, json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
B2 = os.path.join(os.path.dirname(HERE), "showcase", "jigsaw_b2")
OUT = os.path.join(B2, "sheets")


def label(im, text, size):
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("arial.ttf", size)
    except OSError:
        f = ImageFont.load_default()
    d.rectangle([0, 0, len(text) * size * 0.62 + 8, size + 6], fill=(0, 0, 0))
    d.text((4, 2), text, fill=(255, 255, 0), font=f)


def main():
    os.makedirs(OUT, exist_ok=True)
    caps = {json.loads(l)["number"]: json.loads(l) for l in io.open(os.path.join(B2, "captions.jsonl"), encoding="utf-8")}
    chosen = [json.loads(l) for l in io.open(os.path.join(B2, "chosen.jsonl"), encoding="utf-8")]
    clean = [c for c in chosen if not c["subject_failed"] and not c["lettering"] and c["style"] and c["faces"] != "bad"]
    files = {c["number"]: f"{c['number']:03d}-{c['slug']}_s{c['seed']}.png" for c in clean}
    n = 0
    for k in range(0, len(clean), 30):
        sheet = Image.new("RGB", (6 * 256, 5 * 256), "white")
        for i, c in enumerate(clean[k:k + 30]):
            im = Image.open(os.path.join(B2, "raw", files[c["number"]])).convert("RGB").resize((256, 256))
            label(im, str(c["number"]), 22)
            sheet.paste(im, ((i % 6) * 256, (i // 6) * 256))
        n += 1
        sheet.save(os.path.join(OUT, f"sheet_{n:02d}.jpg"), quality=85)
    people = [c for c in clean if caps[c["number"]]["people"]]
    m = 0
    for k in range(0, len(people), 4):
        sheet = Image.new("RGB", (2 * 512, 2 * 512), "white")
        for i, c in enumerate(people[k:k + 4]):
            im = Image.open(os.path.join(B2, "raw", files[c["number"]])).convert("RGB")
            label(im, str(c["number"]), 26)
            sheet.paste(im, ((i % 2) * 512, (i // 2) * 512))
        m += 1
        sheet.save(os.path.join(OUT, f"faces_{m:02d}.jpg"), quality=88)
    json.dump([c["number"] for c in clean], io.open(os.path.join(B2, "clean.json"), "w"), indent=0)
    print(f"clean {len(clean)}: {n} contact sheets, {len(people)} with people on {m} face sheets")


if __name__ == "__main__":
    main()
