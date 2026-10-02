"""Pagouro BE Styles: captions AND artwork bounding boxes from an open-weights vision model (Qwen,
Apache 2.0) through OpenRouter — no commercial API in the chain this time (D-103). One call per image
returns JSON: caption (one plain sentence, lettering quoted), artwork_box (fractions of the image that
bound the artwork itself, excluding mount, border, ruler, colour strip), has_scan_border.
Writes <ledger>.captions.jsonl with caption_source = "machine (<model>, <date>)"; resumable.

    python scripts/caption_qwen.py --ledger <path> [--model qwen/qwen3.6-27b] [--workers 4] [--cap N]
"""
from __future__ import annotations
import argparse, base64, concurrent.futures as cf, io, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", ".env")
PROMPT = ('Return JSON only, no prose: {"caption": "<one plain sentence, at most 30 words, saying what is in the picture: '
          'the main subject, what it is doing, the setting, any large lettering quoted exactly; do not name the artist, '
          'style, era or medium; do not begin with The image or This>", "artwork_box": [x0, y0, x1, y1], '
          '"has_scan_border": true|false}. artwork_box is the box, as fractions of width and height from 0 to 1, '
          'that bounds the artwork itself and excludes any mount, mat, frame, ruler, colour strip or background '
          'table; if the artwork fills the whole picture use [0,0,1,1].')


def load_key():
    for line in io.open(ENV, encoding="utf-8"):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OPENROUTER_API_KEY")


def small_jpeg(path, max_side=640):
    from PIL import Image
    im = Image.open(path).convert("RGB"); im.thumbnail((max_side, max_side))
    b = io.BytesIO(); im.save(b, "JPEG", quality=85); return b.getvalue()


def one(key, model, path, tries=3, expect=""):
    data = base64.b64encode(small_jpeg(path)).decode()
    prompt = PROMPT
    if expect:
        prompt = PROMPT[:-1] + f', "on_topic": true|false}}. on_topic is true only if the picture clearly shows {expect} as its main content (not a landscape, building, label, map or object that merely relates to it).'
    # Qwen 3.x models "think" before answering; with reasoning on, 240 tokens were eaten by the thinking and the JSON
    # never came (734 of 802 empty on the first ukiyo-e pass). Reasoning off, and room for the answer.
    body = {"model": model, "max_tokens": 700, "temperature": 0.1, "reasoning": {"enabled": False},
            "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}}]}]}
    err = ""
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                                  "HTTP-Referer": "https://pagouro.com", "X-Title": "Pagouro BE Styles captions"})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            txt = d["choices"][0]["message"]["content"] or ""
            m = re.search(r"\{.*\}", txt, re.S)
            v = json.loads(m.group(0)) if m else {}
            cap = str(v.get("caption", "")).strip()
            box = v.get("artwork_box")
            if not (isinstance(box, list) and len(box) == 4): box = [0, 0, 1, 1]
            box = [max(0.0, min(1.0, float(x))) for x in box]
            if box[2] - box[0] < 0.3 or box[3] - box[1] < 0.3: box = [0, 0, 1, 1]
            if cap: return {"caption_content": cap, "artwork_box": box, "has_scan_border": bool(v.get("has_scan_border")),
                            "on_topic": (None if not expect else bool(v.get("on_topic"))), "usage": d.get("usage", {})}
            err = "empty caption"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:120]; time.sleep(2 * (i + 1))
    return {"error": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--model", default="qwen/qwen3.6-27b")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cap", type=int, default=100000)
    ap.add_argument("--expect", default="", help="the subject the corpus should show; adds an on_topic yes/no to each row")
    a = ap.parse_args()
    key = load_key()
    out_path = a.ledger + ".captions.jsonl"; done = set()
    if os.path.exists(out_path):
        for l in io.open(out_path, encoding="utf-8"): done.add(json.loads(l)["id"])
    folder = os.path.dirname(a.ledger); todo = []
    for l in io.open(a.ledger, encoding="utf-8"):
        r = json.loads(l)
        if r["id"] in done: continue
        p = os.path.join(folder, r["file"])
        if os.path.exists(p): todo.append((r["id"], p))
    todo = todo[:a.cap]
    print(f"{len(done)} done; {len(todo)} to caption with {a.model}", flush=True)
    n = fail = 0; tin = tout = 0; t0 = time.time()
    with io.open(out_path, "a", encoding="utf-8", newline="\n") as out, cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, key, a.model, p, 3, a.expect): oid for oid, p in todo}
        for f in cf.as_completed(futs):
            oid = futs[f]; v = f.result()
            if "error" in v: fail += 1; print("  failed", oid, v["error"][:80], flush=True); continue
            u = v.pop("usage", {}); tin += u.get("prompt_tokens") or 0; tout += u.get("completion_tokens") or 0
            out.write(json.dumps({"id": oid, **v, "caption_source": f"machine ({a.model}, {time.strftime('%Y-%m-%d')})"}, ensure_ascii=False) + "\n"); out.flush(); n += 1
            if n % 100 == 0: print(f"  {n} done, {time.time()-t0:,.0f}s, tokens in {tin:,} out {tout:,}", flush=True)
    print(f"done: {n} captions, {fail} failed; tokens in {tin:,} out {tout:,}; {time.time()-t0:,.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
