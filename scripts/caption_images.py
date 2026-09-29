"""Pagouro BE: machine-written content captions for the poster corpus (D-98).

For each ledger row without a `caption_content`, send the image (downscaled to <= 512 px, JPEG)
to a vision model through OpenRouter and ask for ONE plain sentence describing what is in the
picture (subject, action, setting, any large lettering, quoted). The answer is stored on the
row as `caption_content` with `caption_source` = "machine (<model>, <date>)", the same labelling
CommonCanvas gives its BLIP-2 captions. Titles, artists and dates stay in their own fields; the
training caption is assembled later by build_be_trainset.py.

    python scripts/caption_images.py --ledger <path> [--model google/gemini-2.5-flash-lite] [--cap N] [--workers 4]

Writes <ledger>.captions.jsonl (id -> caption_content, caption_source, usage) so a rerun resumes.
Key: OPENROUTER_API_KEY from PAGOURO_BUILD/.env (never printed).
"""
from __future__ import annotations
import argparse, base64, concurrent.futures as cf, io, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", ".env")
PROMPT = ("Describe what is in this picture in one plain sentence of at most 30 words: the main subject, "
          "what it is doing, the setting, and any large lettering (quote the words exactly). "
          "Do not name the artist, the style, the era or the medium. Do not begin with 'The image' or 'This'.")


def load_key():
    k = os.environ.get("OPENROUTER_API_KEY")
    if k:
        return k
    for line in io.open(ENV, encoding="utf-8"):
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OPENROUTER_API_KEY")


def small_jpeg(path, max_side=512):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return b.getvalue()


def caption_one(key, model, path, tries=3):
    data = base64.b64encode(small_jpeg(path)).decode()
    body = {"model": model, "max_tokens": 80, "temperature": 0.2,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}}]}]}
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                                  "HTTP-Referer": "https://pagouro.com", "X-Title": "Pagouro BE captions"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read())
            text = d["choices"][0]["message"]["content"].strip().replace("\n", " ")
            return text, d.get("usage", {})
        except Exception as e:  # noqa: BLE001
            time.sleep(2 * (i + 1))
            err = str(e)
    return None, {"error": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--model", default="google/gemini-2.5-flash-lite")
    ap.add_argument("--cap", type=int, default=100000)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    key = load_key()
    out_path = a.ledger + ".captions.jsonl"
    done = {}
    if os.path.exists(out_path):
        for line in io.open(out_path, encoding="utf-8"):
            r = json.loads(line)
            done[r["id"]] = r
    folder = os.path.dirname(a.ledger)
    todo = []
    for line in io.open(a.ledger, encoding="utf-8"):
        r = json.loads(line)
        if r["id"] in done:
            continue
        p = os.path.join(folder, r["file"])
        if os.path.exists(p):
            todo.append((r["id"], p))
    todo = todo[:a.cap]
    print(f"{len(done):,} captioned already; {len(todo):,} to do with {a.model}", flush=True)
    n = 0
    tok_in = tok_out = 0
    t0 = time.time()
    with io.open(out_path, "a", encoding="utf-8", newline="\n") as out, cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(caption_one, key, a.model, p): oid for oid, p in todo}
        for f in cf.as_completed(futs):
            oid = futs[f]
            text, usage = f.result()
            if not text:
                print(f"  failed {oid}: {usage}", flush=True)
                continue
            row = {"id": oid, "caption_content": text, "caption_source": f"machine ({a.model}, {time.strftime('%Y-%m-%d')})",
                   "usage": {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens")}}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            tok_in += usage.get("prompt_tokens") or 0
            tok_out += usage.get("completion_tokens") or 0
            n += 1
            if n % 100 == 0:
                print(f"  {n:,} done, {time.time()-t0:,.0f}s, tokens in {tok_in:,} out {tok_out:,}", flush=True)
    print(f"done: {n:,} new captions; tokens in {tok_in:,} out {tok_out:,}; {time.time()-t0:,.0f}s; file {out_path}")


if __name__ == "__main__":
    sys.exit(main())
