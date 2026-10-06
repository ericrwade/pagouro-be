"""Pagouro BE jigsaw batch 2 -> Pagouro Jigsaw: copy the picks into the game.

Takes the judge's clean picks (chosen.jsonl: subject seen, no lettering, poster style, faces not bad), drops the ones
rejected by eye (REJECT, with reasons, from the contact sheets and the full-size face sheets), and writes each
keeper's 2x upscale as a quality-90 JPEG into PAGOURO_PLAY/jigsaw/art/be/b2-NNN-slug.jpg, adding it to pictures.json
with its season (used by the daily calendar). Records the decision in showcase/jigsaw_b2/game_picks.json.

    python scripts/showcase_jigsaw_b2_to_game.py
"""
import io, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
B2 = os.path.join(os.path.dirname(HERE), "showcase", "jigsaw_b2")
GAME = r"C:\Users\Eric Wade\PAGOURO_PLAY\jigsaw\art\be"
GREY = "a grey engraving or photo, not a color poster"
ABSTRACT = "abstract shapes, the subject is not there"
WEAK = "weak or mostly empty composition, poor as a jigsaw"
REJECT = {
    2: "odd pale ovals all over the ice", 13: ABSTRACT, 14: GREY, 38: "garish magenta trees",
    54: "bridge and statues muddled under snow", 64: "too dark for a jigsaw", 66: "awkward split composition",
    86: "the hare is a ghostly blob", 84: GREY,
    105: "foals' legs melted", 118: "grey on grey, too faint for a jigsaw", 122: WEAK,
    137: ABSTRACT, 141: ABSTRACT, 143: ABSTRACT, 150: "a jumble of horse legs", 159: "awkward giant sail",
    169: "odd horse anatomy", 171: GREY, 178: "the elephant's shape is wrong", 182: "the dog is a woolly blob",
    189: "the dog is a strange shape", 194: ABSTRACT,
    195: "whale and boat muddled", 199: "faint grey koala", 203: "the otter is a strange creature",
    205: "odd puppy faces", 225: GREY,
    228: "muddled", 231: "trees hide the Colosseum", 234: ABSTRACT, 247: "camels muddled", 256: GREY, 259: GREY,
    268: WEAK, 272: "wagons muddled", 275: GREY, 278: GREY, 284: WEAK, 285: WEAK, 292: GREY, 297: ABSTRACT,
    299: WEAK, 305: GREY, 306: ABSTRACT, 310: WEAK,
    313: "black and white, too hard as a jigsaw", 318: "too low-contrast", 325: WEAK,
    329: "repetitive stars, too hard as a jigsaw", 341: ABSTRACT, 342: GREY,
}


def main():
    caps = {}
    for l in io.open(os.path.join(B2, "captions.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        caps[r["number"]] = r
    chosen = [json.loads(l) for l in io.open(os.path.join(B2, "chosen.jsonl"), encoding="utf-8")]
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
        stem = f"b2-{n:03d}-{c['slug']}"
        res = f"res://art/be/{stem}.jpg"
        src = os.path.join(B2, "up", f"{n:03d}-{c['slug']}_s{c['seed']}.png")
        Image.open(src).convert("RGB").save(os.path.join(GAME, stem + ".jpg"), quality=90)
        if res not in have:
            pics.append({"file": res, "caption": c["caption"], "category": c["category"], "seed": c["seed"],
                         "season": caps[n]["season"]})
        picks.append({"number": n, "slug": c["slug"], "seed": c["seed"], "kept": True, "file": stem + ".jpg"})
        kept += 1
    pics.sort(key=lambda p: os.path.basename(p["file"]))
    json.dump(pics, io.open(pj, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    json.dump(picks, io.open(os.path.join(B2, "game_picks.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"clean {len(clean)}, rejected by eye {len(clean) - kept}, added {kept}; game now {len(pics)} pictures")


if __name__ == "__main__":
    main()
