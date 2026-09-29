"""Pagouro BE: the human-scoring sample (D-98). Picks 40 gate images blind across arms (16 ft, 12 lora,
12 base), one seed per caption so every caption appears once, shuffles them with a fixed seed, writes
384-px JPEG thumbnails and a manifest (evals/results/round1/human_sample/{manifest.json, *.jpg}).
The scoring page shows the caption and the picture and asks subject / style / text yes-no; the code
it produces is decoded by score_human.py against the judge's verdicts for the same files.

    python scripts/make_human_sample.py --gate-dir runs/round1/gate --out evals/results/round1/human_sample
"""
from __future__ import annotations
import argparse, base64, io, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=74)
    ap.add_argument("--mix", default="ft=16,lora=12,base=12", help="arm=count,... summing to 40")
    a = ap.parse_args()
    from PIL import Image
    gate = [json.loads(l) for l in io.open(os.path.join(os.path.dirname(HERE), "evals", "gate40.jsonl"), encoding="utf-8")]
    rng = random.Random(a.seed)
    ids = [g["id"] for g in gate]
    rng.shuffle(ids)
    arms = []
    for part in a.mix.split(","):
        arm, cnt = part.split("=")
        arms += [arm] * int(cnt)
    assert len(arms) == 40, "mix must sum to 40"
    rng.shuffle(arms)
    os.makedirs(a.out, exist_ok=True)
    items = []
    for k, (gid, arm) in enumerate(zip(ids, arms)):
        g = next(x for x in gate if x["id"] == gid)
        seed = rng.randrange(4)
        fn = f"{gid}_s{seed}.png"
        im = Image.open(os.path.join(a.gate_dir, arm, fn)).convert("RGB").resize((384, 384), Image.LANCZOS)
        b = io.BytesIO()
        im.save(b, "JPEG", quality=82)
        thumb = f"{k:02d}.jpg"
        open(os.path.join(a.out, thumb), "wb").write(b.getvalue())
        items.append({"n": k, "thumb": thumb, "arm": arm, "file": fn, "id": gid, "group": g["group"],
                      "caption": g["caption"], "expect_text": g["expect_text"], "b64": base64.b64encode(b.getvalue()).decode()})
    json.dump([{k: v for k, v in it.items() if k != "b64"} for it in items], open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    json.dump(items, open(os.path.join(a.out, "manifest_b64.json"), "w"))
    print(len(items), "items;", sum(len(i["b64"]) for i in items) // 1024, "KB of base64")
    return 0


if __name__ == "__main__":
    sys.exit(main())
