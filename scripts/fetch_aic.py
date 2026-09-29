"""Pagouro BE corpus: the Art Institute of Chicago open-access API (CC0 images, keyless).

Search: public-domain works whose title / classification / medium / terms match a query
("poster", "lithograph"), dated by the museum's own date_start <= --max-year (1928: pre-1929,
public domain in the US; the AIC also marks each as is_public_domain). The IIIF image at 843 px
wide is downloaded, hashed and listed in data/images/aic/ledger.jsonl with title, artist,
date, medium, classification, subject/term titles, credit line, the API URL, the image URL,
licence "CC0 (AIC public domain image; is_public_domain=true)", sha256 and pixel size.
Polite: one request at a time, a pause between, retries.

    python scripts/fetch_aic.py --query poster --cap 3000 [--max-year 1928] [--min-year 1860]

Data root: PAGOURO_DATA env var, else ../PAGOURO_BUILD/data/images (the Pagouro ledgers' home).
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, struct, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("PAGOURO_DATA") or os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", "data", "images")
OUT = os.path.join(os.path.abspath(DATA), "aic")
LEDGER = os.path.join(OUT, "ledger.jsonl")
API = "https://api.artic.edu/api/v1/artworks/search"
IIIF = "https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg"
FIELDS = "id,title,artist_display,artist_title,date_display,date_start,date_end,medium_display,classification_titles,term_titles,subject_titles,is_public_domain,image_id,credit_line,place_of_origin,api_link"
UA = {"User-Agent": "pagouro-be-corpus/1.0 (public-domain poster corpus; one request at a time)"}


def get(url, data=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={**UA, **({"Content-Type": "application/json"} if data else {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            print(f"  retry {i+1}: {e}", flush=True)
            time.sleep(3 * (i + 1))
    return None


def jpeg_size(b: bytes):
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="poster", help="multi_match text over title/classification/medium/terms/subjects")
    ap.add_argument("--medium", default="", help="instead: match_phrase on medium_display (e.g. lithograph)")
    ap.add_argument("--cap", type=int, default=3000)
    ap.add_argument("--max-year", type=int, default=1928)
    ap.add_argument("--min-year", type=int, default=1860)
    ap.add_argument("--limit", type=int, default=100)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    have = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                have.add(json.loads(line)["id"])
            except Exception:  # noqa: BLE001
                pass
    body = {
        "query": {"bool": {"must": [
            {"term": {"is_public_domain": True}},
            {"exists": {"field": "image_id"}},
            {"range": {"date_start": {"gte": a.min_year, "lte": a.max_year}}},
            ({"match_phrase": {"medium_display": a.medium}} if a.medium else
             {"multi_match": {"query": a.query, "fields": ["title", "classification_titles", "medium_display", "term_titles", "subject_titles"]}}),
        ]}},
        "fields": FIELDS.split(","),
        "limit": a.limit,
    }
    new = seen = 0
    page = 1
    with io.open(LEDGER, "a", encoding="utf-8", newline="\n") as led:
        while new < a.cap:
            body["page"] = page
            raw = get(API, json.dumps(body).encode())
            if not raw:
                break
            d = json.loads(raw)
            total = (d.get("pagination") or {}).get("total")
            rows = d.get("data") or []
            if not rows:
                break
            for r in rows:
                seen += 1
                if new >= a.cap:
                    break
                oid = f"aic_{r['id']}"
                if oid in have or not r.get("image_id") or not r.get("is_public_domain"):
                    continue
                ys = r.get("date_start")
                if ys is None or ys > a.max_year or (r.get("date_end") or ys) > a.max_year:
                    continue
                url = IIIF.format(image_id=r["image_id"])
                img = get(url)
                time.sleep(0.6)
                if not img or len(img) < 5000:
                    print(f"  skip {oid}: no image", flush=True)
                    continue
                w, h = jpeg_size(img)
                fn = f"{oid}.jpg"
                with open(os.path.join(OUT, fn), "wb") as f:
                    f.write(img)
                row = {
                    "source": "aic", "id": oid, "file": fn, "title": r.get("title"),
                    "artist": r.get("artist_title") or r.get("artist_display"), "artist_display": r.get("artist_display"),
                    "date": r.get("date_display"), "year": ys, "year_end": r.get("date_end"),
                    "medium": r.get("medium_display"), "classification": r.get("classification_titles"),
                    "terms": r.get("term_titles"), "subjects": r.get("subject_titles"),
                    "place": r.get("place_of_origin"), "credit": r.get("credit_line"),
                    "item_url": f"https://www.artic.edu/artworks/{r['id']}", "api_url": r.get("api_link"), "image_url": url,
                    "license": "CC0 (AIC public domain image; is_public_domain=true)",
                    "rights_basis": f"AIC is_public_domain=true; date_start {ys} <= {a.max_year} (pre-1929 US public domain)",
                    "sha256": hashlib.sha256(img).hexdigest(), "bytes": len(img), "width": w, "height": h,
                    "fetched": time.strftime("%Y-%m-%d"),
                }
                led.write(json.dumps(row, ensure_ascii=False) + "\n")
                led.flush()
                have.add(oid)
                new += 1
                if new % 50 == 0:
                    print(f"  {new:,} kept ({seen:,} seen of {total}) page {page}", flush=True)
            page += 1
            if total and seen >= int(total):
                break
            time.sleep(1.0)
    print(f"done: {new:,} new; ledger {len(have):,} items; query={a.query!r} years {a.min_year}-{a.max_year}; files in {OUT}")


if __name__ == "__main__":
    sys.exit(main())
