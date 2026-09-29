"""Round 3 (D-99 follow-up): shift the model's prior away from lettering by sampling the lettering-free
images more often. Duplicates every training file whose caption ends with ", no lettering" k-1 times
(physical copies, so the diffusers imagefolder loader sees distinct rows) and appends the rows to
metadata.jsonl. Idempotent: skips files already duplicated.

    python scripts/upweight_nolettering.py --dir <be_train/512> --k 3
"""
from __future__ import annotations
import argparse, io, json, os, shutil, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--k", type=int, default=3)
    a = ap.parse_args()
    meta_path = os.path.join(a.dir, "metadata.jsonl")
    rows = [json.loads(l) for l in io.open(meta_path, encoding="utf-8")]
    have = {r["file_name"] for r in rows}
    base = [r for r in rows if r["text"].endswith(", no lettering") and "_dup" not in r["file_name"]]
    added = 0
    with io.open(meta_path, "a", encoding="utf-8", newline="\n") as out:
        for r in base:
            stem, ext = os.path.splitext(r["file_name"])
            for i in range(2, a.k + 1):
                name = f"{stem}_dup{i}{ext}"
                if name in have:
                    continue
                shutil.copyfile(os.path.join(a.dir, r["file_name"]), os.path.join(a.dir, name))
                out.write(json.dumps({"file_name": name, "text": r["text"]}, ensure_ascii=False) + "\n")
                have.add(name)
                added += 1
    print(f"lettering-free base files {len(base)}; added {added} copies (k={a.k}); metadata rows now {len(rows) + added}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
