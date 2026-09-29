"""Draw 1.0 corpus, slice one: The Met Open Access (CC0), the 1880–1928 print world (O-28) plus
the hermit crab / shell subjects (D-67). Standard library only.

The Met's collection API needs no key and marks each object `isPublicDomain` (CC0 images).
Every kept image gets a row in data/images/ledger.jsonl: objectID, title, artist, date, medium,
department, classification, tags, the object URL, the image URL, licence "CC0 (The Met Open
Access)", sha256 and pixel size. Objects are kept only when isPublicDomain is true and
objectEndDate <= 1928 (O-28's era; also satisfies D-34 pre-2022 trivially). Rate: one request
at a time with a short pause; the Met asks for <= 80/s, we use ~4/s.

    python scripts/fetch_draw_corpus.py --cap 2000            -> data/images/met/<id>.jpg + ledger rows
    python scripts/fetch_draw_corpus.py --queries "hermit crab" "shell" --cap 300
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import struct
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "images", "met")
LEDGER = os.path.join(ROOT, "data", "images", "ledger.jsonl")
API = "https://collectionapi.metmuseum.org/public/collection/v1"
UA = {"User-Agent": "pagouro-corpus-builder/1.0 (+https://github.com/ericrwade/pagouro)"}

QUERIES = ["title:trade card", "title:advertisement", "title:poster", "title:catalogue", "title:cartouche",
           "title:ornament", "title:border", "title:alphabet", "title:frontispiece", "title:vignette",
           "title:label", "title:monogram", "title:bookplate", "title:ex libris", "title:letterhead",
           "title:seed catalogue", "title:fashion plate", "title:shell", "title:crab", "title:hermit crab",
           "title:seashell", "title:conch", "title:nautilus", "title:crustacea", "title:mollusc",
           "crab", "hermit crab", "seashell", "chromolithograph", "trade card"]


def get_json(url: str, tries: int = 4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(2 * (i + 1))


def get_bytes(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                return b""
            time.sleep(2 * (i + 1))
    return b""


def jpeg_size(data: bytes) -> tuple[int, int] | None:
    """Width/height from JPEG SOF markers, no Pillow."""
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1; continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2; continue
        ln = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + ln
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", nargs="*", default=QUERIES)
    ap.add_argument("--cap", type=int, default=2000, help="max new images this run")
    ap.add_argument("--max-year", type=int, default=1928)
    ap.add_argument("--per-query", type=int, default=400)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    have = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            if line.strip():
                have.add(json.loads(line)["objectID"])
    print(f"ledger has {len(have):,} images; fetching up to {a.cap:,} more, objects dated <= {a.max_year}")
    new = 0
    seen_ids: set[int] = set(have)
    with io.open(LEDGER, "a", encoding="utf-8", newline="\n") as led:
        for q in a.queries:
            if new >= a.cap:
                break
            # The search index's isPublicDomain filter is broken (crab: 226 -> 3), so search on hasImages only
            # and check isPublicDomain on each object. "title:" prefix restricts a phrase to titles.
            qq, extra = (q[6:], "&title=true") if q.startswith("title:") else (q[7:], "&artistOrCulture=true") if q.startswith("artist:") else (q, "")
            res = get_json(f"{API}/search?hasImages=true{extra}&q={urllib.parse.quote(qq)}")
            ids = (res or {}).get("objectIDs") or []
            print(f"  '{q}': {len(ids):,} objects with images (PD checked per object)", flush=True)
            kept_q = 0
            for oid in ids[: a.per_query * 3]:
                if new >= a.cap or kept_q >= a.per_query:
                    break
                if oid in seen_ids:
                    continue
                seen_ids.add(oid)
                time.sleep(0.25)
                o = get_json(f"{API}/objects/{oid}")
                if not o or not o.get("isPublicDomain") or not o.get("primaryImageSmall"):
                    continue
                end = o.get("objectEndDate") or 0
                if not end or end > a.max_year:
                    continue
                data = get_bytes(o["primaryImageSmall"])
                size = jpeg_size(data)
                if not size or min(size) < 200:
                    continue
                path = os.path.join(OUT, f"{oid}.jpg")
                io.open(path, "wb").write(data)
                row = {"objectID": oid, "title": o.get("title"), "artist": o.get("artistDisplayName"),
                       "date": o.get("objectDate"), "end_year": end, "medium": o.get("medium"),
                       "department": o.get("department"), "classification": o.get("classification"),
                       "tags": [t.get("term") for t in (o.get("tags") or [])], "query": q,
                       "object_url": o.get("objectURL"), "image_url": o.get("primaryImageSmall"),
                       "license": "CC0 (The Met Open Access; isPublicDomain=true)", "sha256": hashlib.sha256(data).hexdigest(),
                       "width": size[0], "height": size[1], "bytes": len(data),
                       "file": os.path.relpath(path, ROOT).replace("\\", "/"), "retrieved": time.strftime("%Y-%m-%d")}
                led.write(json.dumps(row, ensure_ascii=False) + "\n"); led.flush()
                new += 1; kept_q += 1
                if new % 50 == 0:
                    print(f"    {new:,} kept so far", flush=True)
    print(f"done: {new:,} new images; ledger {len(seen_ids):,} objects seen; files in {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
