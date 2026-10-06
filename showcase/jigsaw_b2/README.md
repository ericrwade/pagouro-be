# Pagouro BE — jigsaw batch 2 (2026-10-06)

New pictures for Pagouro Jigsaw toward a year of daily puzzles (Eric: "I'd be happy knowing we have a years worth of
pictures"), drawn by **Pagouro BE 1.0** (the frozen, released model, unchanged).

## How they were made

- Captions: `scripts/showcase_jigsaw_b2_prompts.py` → `captions.jsonl` (365 captions, each tagged with a season for
  the daily calendar: 70 winter, 66 spring, 30 summer, 199 any; no living person, no trademark, no drinking or
  smoking; none repeats a picture already in the game).
- Generation: same pipeline and settings as batch 1 (`scripts/runpod/showcase_gen.sh|.py` via
  `scripts/runpod/jigsaw_b2_pod.sh`: diffusers, CommonCanvas-S-C config + the BE UNet, fp16, DPM++ 2M, 30 steps,
  guidance 7, 512x512, the batch 1 negative prompt). Seeds 1000-1011 for the 41 captions with people, 1000-1007 for
  the other 324: **3,084 pictures**, every one upscaled 2x (RealESRGAN_x2plus, `scripts/runpod/upscale2x.py`).
- Pod: 1x A100 SXM 80 GB (RunPod, secure, $1.59/h) `ovyrslc24oye5f`, 2026-10-06 16:43Z, about 1 h 40 min, about
  **$2.65**; deleted after the download. Plan and price posted on Pagouro issue #2 first.
- Home: all 3,084 originals (`SHA256SUMS`, verified on the desk) and the 222 keeper upscales (`KEEP_SHA256`, hashed
  on the pod, verified on the desk). The other upscales were not needed and were not fetched.
- Judge: `scripts/showcase_judge.py` (google/gemini-2.5-flash, 4.95M tokens in, 0.24M out, about **$2.07**).
  Over all 3,084: subject 2,195, lettering 1,754. Of the 365 picks, **274** passed every check (subject, faces,
  no lettering, poster style) — `clean.json`.
- **Eye check** of all 274 at contact-sheet size (`scripts/showcase_jigsaw_b2_sheets.py`) and every picture with
  people at full size: 52 rejected (grey engravings and photos, abstract results, broken animal anatomy, weak or empty
  compositions; reasons in `game_picks.json` and `scripts/showcase_jigsaw_b2_to_game.py`). **222 went into the game**
  as `PAGOURO_PLAY/jigsaw/art/be/b2-NNN-slug.jpg` (40 winter, 49 spring, 19 summer, 114 any), for 382 in all.
- The game places them on a seasonal daily calendar from 2026-11-17 (`PAGOURO_PLAY/tools_src/plan_year_calendar.py`,
  `PAGOURO_PLAY/docs/DAILY_CALENDAR.md`).

Batch total about **$4.70**.

## Rights

Outputs of Pagouro BE are CC0, like every BE output.

## Files

Tracked: this README, `captions.jsonl`, `verdicts.jsonl`, `chosen.jsonl`, `clean.json`, `judge_summary.txt`,
`game_picks.json`, `SHA256SUMS` (512-px originals), `KEEP_SHA256` (keeper upscales). Local only (gitignored):
`raw/` (3,084 originals + meta.json), `up/` (222 upscales), `sheets/` (contact sheets).
