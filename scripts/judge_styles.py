"""Pagouro BE Styles gate judge (D-103). For each style's gate folder, a vision model answers, per picture:
  subject            the thing the caption asks for is clearly recognisable (strict)
  style_match        the picture matches the style's one-line description from styles.json
  anatomy_ok         (anatomy captions only) faces: two eyes, one nose, one mouth, roughly symmetric; hands: five digits
                     per visible hand; bodies: one head, two arms, two legs — null for other captions
  unasked_lettering  any lettering or word-like marks present
Judge is arm-blind. Writes verdicts_<style>.jsonl and summary.md under --gate-root.

    python scripts/judge_styles.py --gate-root runs/styles --styles base_gate rockart ukiyoe ... [--model google/gemini-2.5-flash]
"""
from __future__ import annotations
import argparse, base64, concurrent.futures as cf, io, json, os, sys, time, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); BE = os.path.dirname(HERE)
ENV = os.path.join(BE, "..", "PAGOURO_BUILD", ".env")
RUBRIC = ("You are judging a generated picture against the caption it was made from. Be strict.\n"
          "Caption: {caption}\nIntended style: {style}\n"
          "Answer in JSON only with keys subject, style_match, anatomy_ok, unasked_lettering, note.\n"
          "subject: true only if the main thing the caption asks for is clearly recognisable as a person would name it.\n"
          "style_match: true if the picture matches the intended style description; false if it looks like a photograph, a 3D render, or a different style.\n"
          "anatomy_ok: {anatomy_rule}\n"
          "unasked_lettering: true if the picture contains any lettering, words or word-like marks (the caption asked for none).\n"
          "note: one short sentence saying what you actually see.")
ANAT = ("judge the anatomy strictly: a face must have two eyes, one nose and one mouth in roughly symmetric positions; "
        "each visible hand must have exactly five digits; a body must have one head, two arms and two legs; true only if everything visible passes")


def key():
    for l in io.open(ENV, encoding="utf-8"):
        if l.startswith("OPENROUTER_API_KEY="): return l.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no key")


def b64(p):
    from PIL import Image
    im = Image.open(p).convert("RGB"); im.thumbnail((512, 512)); b = io.BytesIO(); im.save(b, "JPEG", quality=85)
    return base64.b64encode(b.getvalue()).decode()


def judge(k, model, path, caption, style_desc, anatomy, tries=3):
    body = {"model": model, "max_tokens": 180, "temperature": 0.0, "messages": [{"role": "user", "content": [
        {"type": "text", "text": RUBRIC.format(caption=caption, style=style_desc, anatomy_rule=(ANAT if anatomy else "null (this caption is not an anatomy test)"))},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(path)}"}}]}]}
    err = ""
    for i in range(tries):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json", "HTTP-Referer": "https://pagouro.com", "X-Title": "Pagouro BE Styles gate"})
            with urllib.request.urlopen(req, timeout=90) as r: d = json.loads(r.read())
            t = d["choices"][0]["message"]["content"]; t = t[t.find("{"): t.rfind("}") + 1]; v = json.loads(t)
            return {"subject": bool(v.get("subject")), "style_match": bool(v.get("style_match")), "anatomy_ok": (None if v.get("anatomy_ok") is None else bool(v.get("anatomy_ok"))),
                    "unasked_lettering": bool(v.get("unasked_lettering")), "note": str(v.get("note", ""))[:200]}
        except Exception as e:  # noqa: BLE001
            err = str(e)[:100]; time.sleep(2 * (i + 1))
    return {"error": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-root", required=True)
    ap.add_argument("--styles", nargs="+", required=True)
    ap.add_argument("--model", default="google/gemini-2.5-flash")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    k = key(); styles = json.load(io.open(os.path.join(BE, "styles.json"), encoding="utf-8"))
    lines = ["| style | n | subject | style match | anatomy ok (anatomy captions) | unasked lettering |", "|---|---|---|---|---|---|"]
    for st in a.styles:
        d = os.path.join(a.gate_root, st, "gate"); meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
        desc = styles.get(st, {}).get("judge", "a Belle Époque lithographic poster: flat colour planes, bold outlines, poster paper")
        out_path = os.path.join(a.gate_root, f"verdicts_{st}.jsonl"); done = {}
        if os.path.exists(out_path):
            for l in io.open(out_path, encoding="utf-8"): r = json.loads(l); done[r["file"]] = r
        todo = [m for m in meta if m["file"] not in done]
        print(f"{st}: {len(done)} judged, {len(todo)} to judge", flush=True)
        with io.open(out_path, "a", encoding="utf-8", newline="\n") as out, cf.ThreadPoolExecutor(a.workers) as ex:
            futs = {ex.submit(judge, k, a.model, os.path.join(d, m["file"]), m["caption"], desc, m.get("anatomy", False)): m for m in todo}
            for f in cf.as_completed(futs):
                m = futs[f]; v = f.result()
                if "error" in v: print("  failed", m["file"], v["error"][:60], flush=True); continue
                r = {"file": m["file"], "id": m["id"], "group": m["group"], "caption": m["caption"], **v}
                out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush(); done[m["file"]] = r
        n = len(done); subj = sum(r["subject"] for r in done.values()); sm = sum(r["style_match"] for r in done.values())
        an = [r["anatomy_ok"] for r in done.values() if r["anatomy_ok"] is not None]; let = sum(r["unasked_lettering"] for r in done.values())
        lines.append(f"| {st} | {n} | {subj}/{n} ({100*subj/max(n,1):.0f} %) | {sm}/{n} ({100*sm/max(n,1):.0f} %) | {sum(an)}/{len(an)} | {let}/{n} ({100*let/max(n,1):.0f} %) |")
    md = "\n".join(lines); print(md)
    io.open(os.path.join(a.gate_root, "summary.md"), "w", encoding="utf-8", newline="\n").write(f"# Styles gate — judge {a.model}, {time.strftime('%Y-%m-%d')}\n\n{md}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
