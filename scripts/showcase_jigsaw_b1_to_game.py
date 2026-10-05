"""Pagouro BE jigsaw batch 1 -> Pagouro Jigsaw: copy the picks into the game.

Takes the judge's clean picks (chosen.jsonl: subject seen, no lettering, poster style, faces not bad), drops the
ones rejected by eye (REJECT, with reasons), and writes each keeper's 2x upscale as a quality-90 JPEG into
PAGOURO_PLAY/jigsaw/art/be/b1-NNN-slug.jpg, adding it to pictures.json. Records the decision in
showcase/jigsaw_b1/game_picks.json.

    python scripts/showcase_jigsaw_b1_to_game.py
"""
import io, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.join(os.path.dirname(HERE), "showcase", "jigsaw_b1")
GAME = r"C:\Users\Eric Wade\PAGOURO_PLAY\jigsaw\art\be"
REJECT = {
    17: "clown face smeared", 46: "topiary is an abstract jumble", 49: "woman's face is off",
    60: "cyclist reads as nude", 67: "dark smudge on the back of the woman's head reads as a face",
    77: "too photographic", 82: "too photographic", 105: "ship muddled", 110: "weak composition",
    128: "airship and mast muddled", 129: "airship is a white blob", 132: "hangar muddled",
}


def main():
    chosen = [json.loads(l) for l in io.open(os.path.join(B1, "chosen.jsonl"), encoding="utf-8")]
    clean = [c for c in chosen if not c["subject_failed"] and not c["lettering"] and c["style"] and c["faces"] != "bad"]
    pj = os.path.join(GAME, "pictures.json")
    pics = json.load(io.open(pj, encoding="utf-8"))
    have = {p["file"] for p in pics}
    kept, picks = 0, []
    for c in clean:
        n = c["number"]
        if n in REJECT:
            picks.append({"number": n, "slug": c["slug"], "seed": c["seed"], "kept": False, "why": REJECT[n]})
            continue
        stem = f"b1-{n:03d}-{c['slug']}"
        res = f"res://art/be/{stem}.jpg"
        Image.open(os.path.join(B1, "up", c["file_raw"])).convert("RGB").save(os.path.join(GAME, stem + ".jpg"), quality=90)
        if res not in have:
            pics.append({"file": res, "caption": c["caption"], "category": c["category"], "seed": c["seed"]})
        picks.append({"number": n, "slug": c["slug"], "seed": c["seed"], "kept": True, "file": stem + ".jpg"})
        kept += 1
    pics.sort(key=lambda p: os.path.basename(p["file"]))
    json.dump(pics, io.open(pj, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    json.dump(picks, io.open(os.path.join(B1, "game_picks.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"clean {len(clean)}, rejected by eye {len(clean) - kept}, added {kept}; game now {len(pics)} pictures")


if __name__ == "__main__":
    main()
