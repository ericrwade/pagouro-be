"""Pagouro BE Styles corpus: Wikimedia Commons, by category walk, with the licence read per file.

    python scripts/fetch_commons.py --style rockart --category "Petroglyphs in the United States" --category "Pictographs in the United States" --depth 3 --cap 800

Keeps a file only when its extmetadata licence is one of CC0, Public domain, CC BY (any version) or
CC BY-SA (any version); records LicenseShortName, LicenseUrl, Artist, Credit, Attribution and the
file page URL, so every row carries the attribution the licence asks for. Downloads a 1280-px
rendition. Throttled to one request per 1.2 s with a descriptive User-Agent (Commons rate-limits
anonymous bursts with HTTP 429; on 429 it sleeps 30 s and retries). Resumable by file title.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, struct, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.environ.get("PAGOURO_DATA") or os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", "data", "images"))
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "pagouro-be-styles/1.0 (https://github.com/ericrwade/pagouro-be; licensed training corpus; one request per second)"}
OK = ("cc0", "public domain", "pd", "cc by", "cc-by", "cc by-sa", "cc-by-sa")
BAD = ("nc", "nd", "gfdl only", "fal")


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429: print("  429, sleeping 30 s", flush=True); time.sleep(30)
            else: print(f"  http {e.code}", flush=True); time.sleep(3)
        except Exception as e:  # noqa: BLE001
            print(f"  retry {i+1}: {str(e)[:80]}", flush=True); time.sleep(4 * (i + 1))
    return None


def api(params):
    params = dict(params, format="json"); time.sleep(1.2)
    raw = get(API + "?" + urllib.parse.urlencode(params))
    return json.loads(raw) if raw else None


def licence_ok(short):
    s = (short or "").lower()
    if not s or any(b in s for b in BAD): return False
    return any(o in s for o in OK)


def jpeg_size(b):
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF: i += 1; continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9]); return w, h
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True)
    ap.add_argument("--category", action="append", required=True)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--cap", type=int, default=800)
    ap.add_argument("--width", type=int, default=1280)
    a = ap.parse_args()
    out = os.path.join(DATA, "styles", a.style); os.makedirs(out, exist_ok=True)
    ledger = os.path.join(out, "ledger.jsonl")
    have = set()
    if os.path.exists(ledger):
        for l in io.open(ledger, encoding="utf-8"):
            try: have.add(json.loads(l)["title"])
            except Exception: pass
    seen_cats, files = set(), {}
    def walk(cat, depth):
        if cat in seen_cats or depth > a.depth: return
        seen_cats.add(cat); cont = {}
        while True:
            d = api({"action": "query", "list": "categorymembers", "cmtitle": cat, "cmlimit": "500", "cmtype": "file|subcat", **cont})
            if not d: return
            for m in d["query"]["categorymembers"]:
                if m["ns"] == 6: files.setdefault(m["title"], cat)
                elif m["ns"] == 14: walk(m["title"], depth + 1)
            if "continue" in d: cont = d["continue"]
            else: break
    for c in a.category:
        walk(c if c.startswith("Category:") else "Category:" + c, 0)
    titles = [t for t in files if t not in have and t.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))]
    print(f"categories {len(seen_cats)}, candidate files {len(files)}, to fetch {len(titles)}", flush=True)
    new = rej = 0
    with io.open(ledger, "a", encoding="utf-8", newline="\n") as led:
        for i in range(0, len(titles), 20):
            if new >= a.cap: break
            d = api({"action": "query", "prop": "imageinfo", "iiprop": "extmetadata|url|size|sha1", "iiurlwidth": str(a.width), "titles": "|".join(titles[i:i+20])})
            if not d: continue
            for p in d["query"]["pages"].values():
                if new >= a.cap: break
                ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
                short = (em.get("LicenseShortName") or {}).get("value", "")
                if not licence_ok(short): rej += 1; continue
                url = ii.get("thumburl") or ii.get("url")
                if not url: continue
                data = get(url); time.sleep(1.2)
                if not data or len(data) < 5000: continue
                w, h = jpeg_size(data) if url.lower().endswith((".jpg", ".jpeg")) else (ii.get("thumbwidth"), ii.get("thumbheight"))
                safe = hashlib.md5(p["title"].encode()).hexdigest()[:12]
                fn = f"commons_{safe}.jpg"; open(os.path.join(out, fn), "wb").write(data)
                strip = lambda k: (em.get(k) or {}).get("value", "")
                row = {"source": "commons", "style": a.style, "id": f"commons_{safe}", "file": fn, "title": p["title"],
                       "page_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(p['title'].replace(' ', '_'))}",
                       "category": files.get(p["title"]), "license": short, "license_url": strip("LicenseUrl"),
                       "artist": strip("Artist")[:200], "credit": strip("Credit")[:200], "attribution": strip("Attribution")[:200],
                       "description": strip("ImageDescription")[:300], "date": strip("DateTimeOriginal"),
                       "image_url": url, "original_sha1": ii.get("sha1"), "sha256": hashlib.sha256(data).hexdigest(),
                       "bytes": len(data), "width": w, "height": h, "fetched": time.strftime("%Y-%m-%d")}
                led.write(json.dumps(row, ensure_ascii=False) + "\n"); led.flush(); have.add(p["title"]); new += 1
                if new % 50 == 0: print(f"  {new} kept, {rej} rejected by licence", flush=True)
    print(f"done: {new} new, {rej} rejected by licence; ledger {len(have)}; {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
