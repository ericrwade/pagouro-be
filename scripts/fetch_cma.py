"""Pagouro BE Styles corpus: the Cleveland Museum of Art open-access API (CC0 works only, keyless).

    python scripts/fetch_cma.py --style ukiyoe --query "woodblock" --type Print --cap 1500
    python scripts/fetch_cma.py --style egyptian --query "tomb" --department "Egyptian and Ancient Near Eastern Art" --cap 800

Keeps only rows with share_license_status == "CC0" and an image. Downloads the museum's web image
(~ 900 px long side), hashes it, and writes data/images/styles/<style>/ledger.jsonl with accession
number, title, creator, date, type, department, culture, technique, the API URL, the image URL,
the licence, sha256 and pixel size. Polite: one request at a time with a pause. Resumable by id.
Data root: PAGOURO_DATA env var, else ../PAGOURO_BUILD/data/images.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, struct, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.environ.get("PAGOURO_DATA") or os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", "data", "images"))
API = "https://openaccess-api.clevelandart.org/api/artworks/"
UA = {"User-Agent": "pagouro-be-styles/1.0 (CC0 corpus; one request at a time)"}


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            print(f"  retry {i+1}: {str(e)[:80]}", flush=True); time.sleep(4 * (i + 1))
    return None


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
    ap.add_argument("--query", default="")
    ap.add_argument("--type", default="", help="e.g. Print, Painting, Ceramic")
    ap.add_argument("--department", default="")
    ap.add_argument("--culture", default="")
    ap.add_argument("--cap", type=int, default=1000)
    ap.add_argument("--limit", type=int, default=100)
    a = ap.parse_args()
    out = os.path.join(DATA, "styles", a.style); os.makedirs(out, exist_ok=True)
    ledger = os.path.join(out, "ledger.jsonl")
    have = set()
    if os.path.exists(ledger):
        for l in io.open(ledger, encoding="utf-8"):
            try: have.add(json.loads(l)["id"])
            except Exception: pass
    params = {"cc0": "1", "has_image": "1", "limit": str(a.limit), "skip": "0"}
    if a.query: params["q"] = a.query
    if a.type: params["type"] = a.type
    if a.department: params["department"] = a.department
    if a.culture: params["culture"] = a.culture
    new = seen = 0; skip = 0
    with io.open(ledger, "a", encoding="utf-8", newline="\n") as led:
        while new < a.cap:
            params["skip"] = str(skip)
            raw = get(API + "?" + urllib.parse.urlencode(params))
            if not raw: break
            d = json.loads(raw); rows = d.get("data") or []
            if not rows: break
            for r in rows:
                seen += 1
                if new >= a.cap: break
                oid = f"cma_{r['id']}"
                if oid in have or r.get("share_license_status") != "CC0": continue
                img = (r.get("images") or {}).get("web", {}).get("url") or (r.get("images") or {}).get("print", {}).get("url")
                if not img: continue
                data = get(img); time.sleep(0.5)
                if not data or len(data) < 5000: continue
                w, h = jpeg_size(data)
                fn = f"{oid}.jpg"; open(os.path.join(out, fn), "wb").write(data)
                creators = r.get("creators") or []
                row = {"source": "cma", "style": a.style, "id": oid, "file": fn, "accession": r.get("accession_number"),
                       "title": r.get("title"), "artist": (creators[0].get("description") if creators else None),
                       "date": r.get("creation_date"), "year": r.get("creation_date_earliest"), "year_end": r.get("creation_date_latest"),
                       "type": r.get("type"), "department": r.get("department"), "culture": r.get("culture"), "technique": r.get("technique"),
                       "item_url": r.get("url"), "api_url": f"https://openaccess-api.clevelandart.org/api/artworks/{r['id']}", "image_url": img,
                       "license": "CC0 (Cleveland Museum of Art Open Access; share_license_status=CC0)",
                       "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "width": w, "height": h, "fetched": time.strftime("%Y-%m-%d")}
                led.write(json.dumps(row, ensure_ascii=False) + "\n"); led.flush(); have.add(oid); new += 1
                if new % 100 == 0: print(f"  {new:,} kept ({seen:,} seen of {d.get('info', {}).get('total')})", flush=True)
            skip += len(rows)
            if skip >= int(d.get("info", {}).get("total") or 0): break
            time.sleep(0.8)
    print(f"done: {new:,} new; ledger {len(have):,}; style {a.style}; {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
