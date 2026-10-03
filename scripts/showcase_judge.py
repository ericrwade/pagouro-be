"""Pagouro BE showcase x180 — pick the best of N seeds per caption with a vision judge.

Same pattern as judge_gate.py (OpenRouter, google/gemini-2.5-flash, key read from PAGOURO_BUILD/.env by path,
temperature 0, JSON answer). Per picture: subject (recognisable as the caption names it), style (lithographic
poster of about 1900), lettering (any words or word-like marks present), appeal (1-5), note. The pick per
caption: subject first, then no lettering, then style, then appeal, then the lowest seed. If no seed has the
subject, the best remaining picture is kept and the row is flagged subject_failed.

    python scripts/showcase_judge.py --raw showcase/x180/raw --out showcase/x180 [--workers 6]
Cost: one vision call per picture (540 for 180 x 3), stated on the run line.
"""
from __future__ import annotations
import argparse, base64, concurrent.futures as cf, io, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", ".env")
RUBRIC = ("You are judging a generated picture against the caption it was made from. Be strict.\n"
          "Caption: {caption}\n"
          "Answer in JSON only, with keys subject, style, lettering, appeal, note.\n"
          "subject: true only if the main thing the caption asks for is clearly recognisable in the picture as a person "
          "would name it; false otherwise.\n"
          "style: true if the picture looks like a lithographic poster of around 1900 (flat colour planes, bold outlines, "
          "poster paper), false if it looks like a photograph, a 3D render, or a modern digital painting.\n"
          "lettering: true if the picture contains any lettering, words or word-like marks (a title band, a caption line, "
          "a signature block, scribbles that imitate text); false if there is none.\n"
          "appeal: an integer 1-5 for how attractive and well composed the picture is as a standalone image to post "
          "(5 = striking, clean, pleasing; 1 = ugly, broken anatomy, muddled).\n"
          "note: one short sentence saying what you actually see.")


def load_key():
    k = os.environ.get("OPENROUTER_API_KEY")
    if k:
        return k
    for line in io.open(ENV, encoding="utf-8"):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OPENROUTER_API_KEY")


def b64(path, max_side=512):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return base64.b64encode(b.getvalue()).decode()


def judge_one(key, model, path, caption, tries=3):
    body = {"model": model, "max_tokens": 200, "temperature": 0.0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": RUBRIC.format(caption=caption)},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(path)}"}}]}]}
    err = "?"
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                                  "HTTP-Referer": "https://pagouro.com", "X-Title": "Pagouro BE showcase"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read())
            txt = d["choices"][0]["message"]["content"].strip()
            txt = txt[txt.find("{"): txt.rfind("}") + 1]
            v = json.loads(txt)
            return {"subject": bool(v.get("subject")), "style": bool(v.get("style")), "lettering": bool(v.get("lettering")),
                    "appeal": int(v.get("appeal") or 0), "note": str(v.get("note", ""))[:200],
                    "usage": {k: d.get("usage", {}).get(k) for k in ("prompt_tokens", "completion_tokens")}}
        except Exception as e:  # noqa: BLE001
            err = str(e)
            time.sleep(2 * (i + 1))
    return {"error": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="google/gemini-2.5-flash")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    key = load_key()
    meta = json.load(open(os.path.join(a.raw, "meta.json"), encoding="utf-8"))
    out_path = os.path.join(a.out, "verdicts.jsonl")
    done = {}
    if os.path.exists(out_path):
        for l in io.open(out_path, encoding="utf-8"):
            r = json.loads(l)
            done[r["file"]] = r
    todo = [m for m in meta if m["file"] not in done]
    print(f"{len(done)} judged, {len(todo)} to judge with {a.model} ({len(todo)} vision calls)", flush=True)
    with io.open(out_path, "a", encoding="utf-8", newline="\n") as out, cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(judge_one, key, a.model, os.path.join(a.raw, m["file"]), m["caption"]): m for m in todo}
        for n, f in enumerate(cf.as_completed(futs), 1):
            m = futs[f]
            v = f.result()
            if "error" in v:
                print("  failed", m["file"], v["error"][:100], flush=True)
                continue
            r = {"file": m["file"], "number": m["number"], "slug": m["slug"], "seed": m["seed"], "caption": m["caption"], **v}
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()
            done[m["file"]] = r
            if n % 50 == 0:
                print(f"  {n}/{len(todo)}", flush=True)
    missing = [m["file"] for m in meta if m["file"] not in done]
    if missing:
        print("UNJUDGED", len(missing), missing[:5])
    # pick per caption
    by = {}
    for m in meta:
        by.setdefault(m["number"], []).append(m)
    chosen = []
    tok_in = tok_out = 0
    for r in done.values():
        tok_in += r["usage"]["prompt_tokens"] or 0
        tok_out += r["usage"]["completion_tokens"] or 0
    for num in sorted(by):
        cands = by[num]
        scored = []
        for m in cands:
            v = done.get(m["file"])
            if not v:
                continue
            scored.append(((v["subject"], not v["lettering"], v["style"], v["appeal"], -m["seed"]), m, v))
        if not scored:
            print("NO VERDICTS for", num)
            continue
        scored.sort(key=lambda t: t[0], reverse=True)
        best_key, best, bv = scored[0]
        why = []
        why.append("subject recognised" if bv["subject"] else "no seed drew the subject; best remaining kept")
        why.append("no lettering" if not bv["lettering"] else "lettering present (every seed had some)" if all(done[c["file"]]["lettering"] for c in cands if c["file"] in done) else "lettering present")
        why.append(f"style {'ok' if bv['style'] else 'weak'}")
        why.append(f"appeal {bv['appeal']}/5")
        others = ", ".join(f"s{done[c['file']]['seed']}: subj={int(done[c['file']]['subject'])} lett={int(done[c['file']]['lettering'])} appeal={done[c['file']]['appeal']}" for c in cands if c["file"] in done and c["file"] != best["file"])
        chosen.append({**{k: best[k] for k in ("number", "slug", "category", "caption", "prompt", "negative", "seed", "steps", "guidance", "sampler", "size")},
                       "file_raw": best["file"], "candidate_seeds": [c["seed"] for c in cands],
                       "chosen_why": "; ".join(why) + (f" (others: {others})" if others else ""),
                       "subject_failed": not bv["subject"], "lettering": bv["lettering"], "style": bv["style"], "appeal": bv["appeal"], "judge_note": bv["note"]})
    with io.open(os.path.join(a.out, "chosen.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for c in chosen:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    n_fail = sum(c["subject_failed"] for c in chosen)
    n_lett = sum(c["lettering"] for c in chosen)
    all_subj = sum(v["subject"] for v in done.values())
    all_lett = sum(v["lettering"] for v in done.values())
    summary = (f"judge {a.model}: {len(done)} pictures judged; subject {all_subj}/{len(done)}, lettering {all_lett}/{len(done)} over all seeds.\n"
               f"chosen {len(chosen)}: subject failed on every seed {n_fail}, lettering present in the chosen picture {n_lett}.\n"
               f"tokens in {tok_in}, out {tok_out}.")
    print(summary)
    io.open(os.path.join(a.out, "judge_summary.txt"), "w", encoding="utf-8", newline="\n").write(summary + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
