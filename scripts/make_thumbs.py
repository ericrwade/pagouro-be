"""Make small raw-RGB thumbnails for the Claude Code slideshow mod (it draws them as half-block cells, which works in any
truecolor terminal; the mod has no image decoder of its own). For every PNG/JPG in a folder, writes
<folder>/thumbs/<name>.rgb (width*height*3 bytes) and thumbs/index.json with sizes and captions.

    python scripts/make_thumbs.py <folder> [--size 120]
Captions come from prompts.jsonl (fields number/slug/prompt or file/caption) or captions.jsonl in the folder, if present.
"""
from __future__ import annotations
import argparse, io, json, os, sys


def captions_for(folder):
    caps = {}
    for fn in ("prompts.jsonl", "captions.jsonl", "chosen.jsonl"):
        p = os.path.join(folder, fn)
        if not os.path.exists(p):
            continue
        for line in io.open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            text = r.get("caption") or r.get("prompt") or r.get("subject") or ""
            for key in ("file", "chosen", "png", "name", "slug"):
                v = r.get(key)
                if isinstance(v, str) and v:
                    caps.setdefault(os.path.splitext(os.path.basename(v))[0], text)
            if r.get("number") is not None and r.get("slug"):
                caps.setdefault(f"{int(r['number']):03d}-{r['slug']}", text)
    return caps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("--size", type=int, default=120)
    a = ap.parse_args()
    from PIL import Image
    out = os.path.join(a.folder, "thumbs"); os.makedirs(out, exist_ok=True)
    caps = captions_for(a.folder); index = []
    files = sorted(f for f in os.listdir(a.folder) if f.lower().endswith((".png", ".jpg", ".jpeg")))
    for f in files:
        im = Image.open(os.path.join(a.folder, f)).convert("RGB")
        w, h = im.size; s = a.size / max(w, h)
        tw, th = max(1, round(w * s)), max(1, round(h * s))
        im = im.resize((tw, th), Image.LANCZOS)
        name = os.path.splitext(f)[0]
        with open(os.path.join(out, name + ".rgb"), "wb") as g:
            g.write(im.tobytes())
        index.append({"name": name, "file": f, "width": tw, "height": th, "caption": caps.get(name, "")})
    json.dump(index, io.open(os.path.join(out, "index.json"), "w", encoding="utf-8"), indent=0)
    print(f"{len(index)} thumbnails in {out}, captions for {sum(1 for r in index if r['caption'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
