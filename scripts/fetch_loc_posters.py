"""Draw 1.0 corpus, slice three (D-74: posters over cards): the Library of Congress "Artists
Posters" collection, keyless JSON API. Standard library only.

For each item: date <= --max-year (1928: pre-1929 publication, public domain in the US), then the
item's own JSON is read for its rights statement; kept only when it says no known restrictions.
The medium JPEG (the `r` tile, ~640 px) is downloaded, hashed and listed in
data/images/loc/ledger.jsonl with title, contributors, date, medium, subjects, the item URL, the
image URL, the rights statement verbatim, sha256 and pixel size. Polite: one request at a time,
a pause between, retries on the API's occasional truncated responses.

    python scripts/fetch_loc_posters.py --cap 1500 [--query cheret] [--max-year 1928]
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import os
import re
import struct
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "images", "loc")
LEDGER = os.path.join(ROOT, "data", "images", "loc", "ledger.jsonl")
UA = {"User-Agent": "pagouro-corpus-builder/1.0 (+https://github.com/ericrwade/pagouro)"}
COLL = "https://www.loc.gov/collections/artists-posters/"


def get(url: str, tries: int = 4) -> bytes:
    """LoC throttles bursts (429, sometimes 520): back off for real and never treat a throttle as an answer."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 520, 502, 503):
                wait = 30 * (i + 1)
                print(f"  throttled ({e.code}); waiting {wait}s", flush=True)
                time.sleep(wait); continue
            if e.code == 404:
                return b""
            time.sleep(5)
        except (http.client.IncompleteRead,) as e:
            time.sleep(5 * (i + 1))
        except Exception:
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"gave up on {url}")


def get_json(url: str):
    b = get(url)
    try:
        return json.loads(b.decode("utf-8", "replace"))
    except Exception:
        return None


def jpeg_size(data: bytes):
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1; continue
        m = data[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2; continue
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def year_of(s) -> int:
    m = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", str(s or ""))
    return int(m.group(1)) if m else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=1500)
    ap.add_argument("--query", default="")
    ap.add_argument("--max-year", type=int, default=1928)
    ap.add_argument("--per-page", type=int, default=100)
    ap.add_argument("--dates", default="1880/1928", help="LoC dates facet, start/end; keeps the walk to the era")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    have = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            if line.strip():
                have.add(json.loads(line)["item_url"])
    new, seen, page = 0, 0, 1
    with io.open(LEDGER, "a", encoding="utf-8", newline="\n") as led:
        while new < a.cap:
            q = f"&q={urllib.parse.quote(a.query)}" if a.query else ""
            d = get_json(f"{COLL}?fo=json&c={a.per_page}&sp={page}{q}&dates={a.dates}")
            if not d or not d.get("results"):
                break
            total = (d.get("pagination") or {}).get("of")
            for r in d["results"]:
                seen += 1
                if new >= a.cap:
                    break
                item = r.get("id") or ""
                if not item.startswith("http") or item in have:
                    continue
                yr = year_of(r.get("date") or r.get("dates"))
                if not yr or yr > a.max_year:
                    continue
                imgs = r.get("image_url") or []
                img_url = next((u for u in imgs if u.endswith("r.jpg")), imgs[-1] if imgs else "")
                if not img_url or "tile.loc.gov" not in img_url:
                    continue
                time.sleep(6.0)                      # LoC crawl pace: they throttled at 3 s; 6 s holds
                try:
                    it = get_json(item.rstrip("/") + "/?fo=json&at=item") or {}     # at=item: 11 KB instead of 50 KB, far fewer truncations
                except RuntimeError as e:            # one dead item must not end the crawl
                    print(f"  skip: {e}", flush=True); continue
                itm = it.get("item") or {}
                rights = itm.get("rights_advisory") or itm.get("rights") or it.get("rights") or ""
                if isinstance(rights, list):
                    rights = " ".join(str(x) for x in rights)
                rights = str(rights).strip()
                if "no known restrictions" not in rights.lower():
                    continue
                time.sleep(1.0)
                try:
                    data = get(img_url)
                except RuntimeError as e:
                    print(f"  skip: {e}", flush=True); continue
                sz = jpeg_size(data)
                if not sz or min(sz) < 200:
                    continue
                key = re.sub(r"[^0-9]", "", item.rstrip("/").rsplit("/", 1)[-1]) or hashlib.md5(item.encode()).hexdigest()[:10]
                path = os.path.join(OUT, f"{key}.jpg")
                io.open(path, "wb").write(data)
                row = {"item_url": item, "title": r.get("title"), "contributors": r.get("contributor") or itm.get("contributors"),
                       "date": r.get("date"), "end_year": yr, "medium": itm.get("medium") or r.get("medium"),
                       "subjects": (r.get("subject") or [])[:12], "image_url": img_url, "rights_as_found": rights,
                       "license": "Public domain (published before 1929; Library of Congress: " + rights[:80] + ")",
                       "source": "Library of Congress, Artists Posters collection", "sha256": hashlib.sha256(data).hexdigest(),
                       "width": sz[0], "height": sz[1], "bytes": len(data), "file": os.path.relpath(path, ROOT).replace("\\", "/"),
                       "retrieved": time.strftime("%Y-%m-%d")}
                led.write(json.dumps(row, ensure_ascii=False) + "\n"); led.flush()
                have.add(item); new += 1
                if new % 50 == 0:
                    print(f"  {new:,} kept ({seen:,} seen of {total}) page {page}", flush=True)
            page += 1
            if total and seen >= int(total):
                break
            time.sleep(0.5)
    print(f"done: {new:,} new posters; ledger {len(have):,} items; files in {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
