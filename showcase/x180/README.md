# Pagouro BE — showcase x180

180 finished pictures from **Pagouro BE 1.0** (the frozen, released Belle Époque poster model), one for each
day of a six-month daily showcase on X (@pagouro). Files `001-<slug>.png` … `180-<slug>.png`, ordered round-robin
across 18 subject categories so consecutive days differ: people 18, landscapes 14, everyday 14, travel 18, fun 16, wine 10, boats 8, lighthouses 7, sailing 8, trains 10, aeroplanes 7, balloons 8, cabaret 10, animals 7, flowers 6, motorcars 6, winter 7, markets 6.

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
  other two seeds' verdicts. Captions where no seed drew the subject: 14 (marked `subject_failed_all_seeds`
  and `*` in `index.md`; the best remaining picture was kept). Chosen pictures in which the judge still saw some
  lettering: 97/180.
- Size: the finals are 1024 px, a 2x Real-ESRGAN upscale (RealESRGAN_x2plus, BSD-3 weights, plain-PyTorch port in `scripts/runpod/upscale2x.py`) of the 512-px originals, which are kept in `512/`.
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
