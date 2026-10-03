"""Pagouro BE showcase x180 — assemble the deliverable folder from the judge's choices.

Reads showcase/x180/chosen.jsonl (from showcase_judge.py) and the raw pictures; copies the chosen 512-px
original of each caption to showcase/x180/512/NNN-slug.png; if showcase/x180/upscaled/ holds a 1024-px
version it becomes the final NNN-slug.png, else the 512 is the final. Writes prompts.jsonl, index.md, README.md.

    python scripts/showcase_x180_finish.py [--raw showcase/x180/raw]
"""
from __future__ import annotations
import argparse, io, json, os, shutil, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BE = os.path.dirname(HERE)
X = os.path.join(BE, "showcase", "x180")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.path.join(X, "raw"))
    ap.add_argument("--sampler-note", default="DPM++ 2M (diffusers DPMSolverMultistepScheduler, fp16, A100)")
    a = ap.parse_args()
    chosen = [json.loads(l) for l in io.open(os.path.join(X, "chosen.jsonl"), encoding="utf-8")]
    assert len(chosen) == 180, len(chosen)
    facts = json.load(io.open(os.path.join(BE, "docs", "facts.json"), encoding="utf-8"))
    up = os.path.join(X, "upscaled")
    have_up = os.path.isdir(up) and len([f for f in os.listdir(up) if f.endswith(".png")]) == 180
    d512 = os.path.join(X, "512")
    os.makedirs(d512, exist_ok=True)
    rows = []
    for c in chosen:
        final = f"{c['number']:03d}-{c['slug']}.png"
        shutil.copyfile(os.path.join(a.raw, c["file_raw"]), os.path.join(d512, final))
        src_final = os.path.join(up, c["file_raw"]) if have_up else os.path.join(d512, final)
        shutil.copyfile(src_final, os.path.join(X, final))
        rows.append({"number": c["number"], "slug": c["slug"], "category": c["category"], "file": final,
                     "file_512": f"512/{final}", "prompt": c["prompt"], "negative_prompt": c["negative"],
                     "caption": c["caption"], "seed": c["seed"], "steps": c["steps"], "guidance": c["guidance"],
                     "sampler": c["sampler"], "size_final": 1024 if have_up else 512,
                     "candidate_seeds": c["candidate_seeds"], "chosen_seed": c["seed"], "chosen_why": c["chosen_why"],
                     "subject_failed_all_seeds": c["subject_failed"], "lettering_in_chosen": c["lettering"],
                     "judge_appeal": c["appeal"], "judge_note": c["judge_note"]})
    with io.open(os.path.join(X, "prompts.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cats = Counter(r["category"] for r in rows)
    n_fail = sum(r["subject_failed_all_seeds"] for r in rows)
    n_lett = sum(r["lettering_in_chosen"] for r in rows)
    lines = ["# Pagouro BE showcase x180 — index", "",
             f"180 pictures, one per day for six months. Final size {'1024 px (Real-ESRGAN x2 of the 512 original in `512/`)' if have_up else '512 px'}. "
             "Prompt shown is the full prompt as given to the model. Rows marked * are captions where none of the three seeds drew the subject (best kept anyway).", "",
             "| # | category | prompt | file | seed |", "|---|---|---|---|---|"]
    for r in rows:
        mark = " *" if r["subject_failed_all_seeds"] else ""
        lines.append(f"| {r['number']:03d}{mark} | {r['category']} | {r['prompt']} | `{r['file']}` | {r['seed']} |")
    io.open(os.path.join(X, "index.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    g = facts["gate"]
    cat_line = ", ".join(f"{k} {v}" for k, v in cats.items())
    readme = f"""# Pagouro BE — showcase x180

180 finished pictures from **Pagouro BE 1.0** (the frozen, released Belle Époque poster model), one for each
day of a six-month daily showcase on X (@pagouro). Files `001-<slug>.png` … `180-<slug>.png`, ordered round-robin
across 18 subject categories so consecutive days differ: {cat_line}.

## How they were made (2026-10-03)

- Model: the shipped `pagouro-be-1.0-fp16.safetensors` (Hugging Face `Pagouro/pagouro-be-1.0`), unchanged.
- Runtime: diffusers `StableDiffusionPipeline` built from the CommonCanvas-S-C config with the BE UNet, fp16,
  on one rented A100 SXM 80 GB (RunPod, pod deleted after download). This is the same pipeline the gate
  numbers were measured with (`scripts/runpod/styles_train.sh`, gate.py) — `scripts/runpod/showcase_gen.py`.
- Settings: prompt `belleposter, Belle Epoque lithograph poster, <caption>`; negative prompt
  `photograph, photo, 3d render, blurry, watermark, text, lettering, words, caption, title, modern, gradient`;
  512x512, DPM++ 2M, 30 steps, guidance 7; seeds 1000, 1001, 1002 per caption (540 pictures).
- Choice: one picture per caption, picked by a vision judge (`google/gemini-2.5-flash` via OpenRouter, rubric in
  `scripts/showcase_judge.py`: subject recognisable, poster style, no lettering, appeal 1-5; subject first, then no
  lettering, then style, then appeal, then the lowest seed). `prompts.jsonl` records every choice and why, with the
  other two seeds' verdicts. Captions where no seed drew the subject: {n_fail} (marked `subject_failed_all_seeds`
  and `*` in `index.md`; the best remaining picture was kept). Chosen pictures in which the judge still saw some
  lettering: {n_lett}/180.
- Size: {'the finals are 1024 px, a 2x Real-ESRGAN upscale (RealESRGAN_x2plus, BSD-3 weights, plain-PyTorch port in `scripts/runpod/upscale2x.py`) of the 512-px originals, which are kept in `512/`.' if have_up else 'the finals are the 512-px originals; the upscale step was skipped (see the session notes on issue #2).'}
- Not retouched, not cropped, not filtered by hand: what the judge picked is what is here.

## What to expect

From `docs/facts.json`: the model draws the asked-for subject about 85 % of the time (human 34/40; judge 131/160),
and its lettering is garbled (unasked word-like marks on ~85 % of gate pictures, asked-for words legible 0/6). The
captions here ask for no words, and the picked seed is the one the judge saw least lettering on, so the rate is
lower in this set — but some pictures still carry glyph-salad bands; that is the model, and the box says so.

## Rights

Outputs of Pagouro BE are **CC0** (`docs/facts.json` → licenses.outputs; model card). Use the pictures freely, credit
welcome but not required. No caption names a living person or a trademark.

## Files

- `NNN-slug.png` — the 180 finals. `512/` — the 512-px originals of the same choices.
- `prompts.jsonl` — one row per picture: number, slug, category, prompt, negative prompt, seed, steps, guidance,
  sampler, candidate seeds, chosen seed and why, judge flags and note.
- `index.md` — number, category, prompt, file, seed.
- `captions.jsonl` — the input list; `verdicts.jsonl` — all 540 judge verdicts; `chosen.jsonl` — the picks;
  `judge_summary.txt` — totals.
- Scripts: `scripts/showcase_x180_prompts.py` (captions), `scripts/runpod/showcase_gen.sh|.py` (pod),
  `scripts/showcase_judge.py` (pick), `scripts/runpod/upscale2x.py` (2x), `scripts/showcase_x180_finish.py` (this folder).
"""
    io.open(os.path.join(X, "README.md"), "w", encoding="utf-8", newline="\n").write(readme)
    print(f"finals {len(rows)} ({'1024' if have_up else '512'} px); subject failed {n_fail}; lettering in chosen {n_lett}; categories {len(cats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
