"""Pagouro BE gate judge (D-98). A vision model scores every gate image against a fixed rubric.

Per image the judge answers three yes/no questions (JSON):
  subject  - is the thing the caption asks for recognisably in the picture?
  style    - does it look like a lithographic poster (flat colour planes, bold contours, poster stock),
             not a photograph or a modern digital painting?
  text     - if the caption asked for specific words, are those words legible in the picture?
             (null when no words were asked for)
plus a one-line note. The judge never sees which arm produced the image. Output: per-image verdicts
(<gate_dir>/verdicts_<arm>.jsonl) and a summary table by arm and caption group, printed and written
to <gate_dir>/summary.md. Cost: one vision call per image; stated on the run line.

    python scripts/judge_gate.py --gate-dir runs/round1/gate --arms base ft lora [--model ...] [--workers 4]
"""
from __future__ import annotations
import argparse, base64, concurrent.futures as cf, io, json, os, sys, time, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(HERE), "..", "PAGOURO_BUILD", ".env")
RUBRIC = ("You are judging a generated picture against the caption it was made from.\n"
          "Caption: {caption}\n"
          "Answer in JSON only, with keys subject, style, text, note.\n"
          "subject: true if the main thing the caption asks for is recognisably present in the picture; false otherwise.\n"
          "style: true if the picture looks like a lithographic poster of around 1900 (flat colour planes, bold outlines, "
          "hand-drawn lettering, poster paper), false if it looks like a photograph, a 3D render, or a modern digital painting.\n"
          "text: {text_rule}\n"
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


def judge_one(key, model, path, caption, expect_text, tries=3):
    text_rule = ("the caption asks for specific words; true if those words are legible in the picture, false if not"
                 if expect_text else "null (the caption asked for no specific words)")
    body = {"model": model, "max_tokens": 160, "temperature": 0.0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": RUBRIC.format(caption=caption, text_rule=text_rule)},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(path)}"}}]}]}
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                                  "HTTP-Referer": "https://pagouro.com", "X-Title": "Pagouro BE gate"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read())
            txt = d["choices"][0]["message"]["content"].strip()
            txt = txt[txt.find("{"): txt.rfind("}") + 1]
            v = json.loads(txt)
            return {"subject": bool(v.get("subject")), "style": bool(v.get("style")),
                    "text": (None if v.get("text") is None else bool(v.get("text"))), "note": str(v.get("note", ""))[:200],
                    "usage": {k: d.get("usage", {}).get(k) for k in ("prompt_tokens", "completion_tokens")}}
        except Exception as e:  # noqa: BLE001
            err = str(e)
            time.sleep(2 * (i + 1))
    return {"error": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-dir", required=True)
    ap.add_argument("--arms", nargs="+", default=["base", "ft", "lora"])
    ap.add_argument("--model", default="google/gemini-2.5-flash")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    key = load_key()
    summary = {}
    for arm in a.arms:
        d = os.path.join(a.gate_dir, arm)
        meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
        gate = {json.loads(l)["id"]: json.loads(l) for l in io.open(os.path.join(os.path.dirname(HERE), "evals", "gate40.jsonl"), encoding="utf-8")}
        out_path = os.path.join(a.gate_dir, f"verdicts_{arm}.jsonl")
        done = {}
        if os.path.exists(out_path):
            for l in io.open(out_path, encoding="utf-8"):
                r = json.loads(l)
                done[r["file"]] = r
        todo = [m for m in meta if m["file"] not in done]
        print(f"{arm}: {len(done)} judged, {len(todo)} to judge with {a.model}", flush=True)
        with io.open(out_path, "a", encoding="utf-8", newline="\n") as out, cf.ThreadPoolExecutor(a.workers) as ex:
            futs = {ex.submit(judge_one, key, a.model, os.path.join(d, m["file"]), m["caption"], gate[m["id"]]["expect_text"]): m for m in todo}
            for f in cf.as_completed(futs):
                m = futs[f]
                v = f.result()
                if "error" in v:
                    print("  failed", m["file"], v["error"][:100], flush=True)
                    continue
                r = {"file": m["file"], "id": m["id"], "group": m["group"], "caption": m["caption"], **v}
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
                out.flush()
                done[m["file"]] = r
        agg = defaultdict(lambda: {"n": 0, "subject": 0, "style": 0, "text_n": 0, "text": 0})
        for r in done.values():
            for g in (r["group"], "ALL"):
                x = agg[g]
                x["n"] += 1
                x["subject"] += r["subject"]
                x["style"] += r["style"]
                if r["text"] is not None:
                    x["text_n"] += 1
                    x["text"] += r["text"]
        summary[arm] = dict(agg)
    lines = ["| arm | group | n | subject | style | legible text |", "|---|---|---|---|---|---|"]
    for arm in a.arms:
        for g in ["ALL", "people", "animals", "objects", "places", "lettering", "impossible"]:
            x = summary[arm].get(g)
            if not x:
                continue
            t = f"{x['text']}/{x['text_n']}" if x["text_n"] else "—"
            lines.append(f"| {arm} | {g} | {x['n']} | {x['subject']}/{x['n']} ({100*x['subject']/x['n']:.0f} %) | {x['style']}/{x['n']} ({100*x['style']/x['n']:.0f} %) | {t} |")
    md = "\n".join(lines)
    print(md)
    io.open(os.path.join(a.gate_dir, "summary.md"), "w", encoding="utf-8", newline="\n").write(f"# Gate summary — judge {a.model}, {time.strftime('%Y-%m-%d')}\n\n{md}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
