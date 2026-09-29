"""Decode the human scoring code against the judge's verdicts for the same 40 files (D-98).

    python scripts/score_human.py --sample evals/results/round1/human_sample --gate-dir runs/round1/gate --code "BE1 00YY- 01YY- ..."

Writes <sample>/human_scores.json and prints human rates by arm plus judge-human agreement.
"""
from __future__ import annotations
import argparse, io, json, os, sys
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--gate-dir", required=True)
    ap.add_argument("--code", required=True)
    a = ap.parse_args()
    items = {it["n"]: it for it in json.load(open(os.path.join(a.sample, "manifest.json"), encoding="utf-8"))}
    toks = a.code.split()
    assert toks[0] == "BE1", "code must start with BE1"
    human = {}
    for t in toks[1:]:
        n = int(t[:2]); s, st, tx = t[2], t[3], t[4]
        human[n] = {"subject": s == "Y", "style": st == "Y", "text": None if tx == "-" else tx == "Y"}
    judge = {}
    for arm in ("base", "ft", "lora"):
        for l in io.open(os.path.join(a.gate_dir, f"verdicts_{arm}.jsonl"), encoding="utf-8"):
            r = json.loads(l); judge[(arm, r["file"])] = r
    rows = []
    by_arm = defaultdict(lambda: {"n": 0, "subject": 0, "style": 0, "text_n": 0, "text": 0})
    agree = {"subject": [0, 0], "style": [0, 0], "text": [0, 0]}
    for n, h in human.items():
        it = items[n]; j = judge[(it["arm"], it["file"])]
        x = by_arm[it["arm"]]; x["n"] += 1; x["subject"] += h["subject"]; x["style"] += h["style"]
        if h["text"] is not None: x["text_n"] += 1; x["text"] += h["text"]
        for k in ("subject", "style"):
            agree[k][1] += 1; agree[k][0] += (h[k] == j[k])
        if h["text"] is not None and j["text"] is not None:
            agree["text"][1] += 1; agree["text"][0] += (h["text"] == j["text"])
        rows.append({"n": n, "arm": it["arm"], "id": it["id"], "group": it["group"], "file": it["file"], "human": h,
                     "judge": {k: j[k] for k in ("subject", "style", "text")}, "judge_note": j.get("note", "")})
    json.dump({"code": a.code, "rows": rows}, open(os.path.join(a.sample, "human_scores.json"), "w", encoding="utf-8"), indent=1)
    print("| arm | n | human: subject | human: style | human: words legible |")
    print("|---|---|---|---|---|")
    for arm in ("base", "ft", "lora"):
        x = by_arm[arm]
        t = f"{x['text']}/{x['text_n']}" if x["text_n"] else "—"
        print(f"| {arm} | {x['n']} | {x['subject']}/{x['n']} ({100*x['subject']/x['n']:.0f} %) | {x['style']}/{x['n']} ({100*x['style']/x['n']:.0f} %) | {t} |")
    print()
    for k, (ok, tot) in agree.items():
        print(f"judge agrees with human on {k}: {ok}/{tot} ({100*ok/tot:.0f} %)" if tot else f"{k}: n/a")
    dis = [r for r in rows if r["human"]["subject"] != r["judge"]["subject"]]
    print("\nsubject disagreements (human / judge):")
    for r in dis:
        print(f"  #{r['n']+1:02d} {r['arm']:4s} {r['id']} human={'Y' if r['human']['subject'] else 'N'} judge={'Y' if r['judge']['subject'] else 'N'}  {r['judge_note'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
