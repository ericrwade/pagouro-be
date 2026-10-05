# Pagouro BE — jigsaw batch 1 (2026-10-04)

New pictures for Pagouro Jigsaw, drawn by **Pagouro BE 1.0** (the frozen, released model, unchanged), on themes Eric
asked for: Paris, nightlife, flowers, boats, gardens, people strolling, cycling, dancing, landscapes of Europe,
salons, castles, sailing and steamships, scientific labs, libraries, airships. No words; faces must be right.

## How they were made

- Captions: `scripts/showcase_jigsaw_b1_prompts.py` → `captions.jsonl` (134 captions, 15 themes; no living
  person, no trademark, no drinking or smoking).
- Generation: same pipeline and settings as x180 (`scripts/runpod/showcase_gen.sh|.py`: diffusers, CommonCanvas-S-C
  config + the BE UNet, fp16, DPM++ 2M, 30 steps, guidance 7, 512x512). Negative prompt = the x180 one plus
  `deformed face, distorted face, asymmetrical eyes, extra fingers, extra limbs, cigarette, smoking, wine glass,
  bottle`. Seeds 1000-1011 for the 50 captions with people, 1000-1007 for the other 84: **1,272 pictures**.
  A same-seed check with the x180 negative prompt drew the same photographic Eiffel Towers and more lettering, so the
  longer negative is not what makes some landmark captions photographic.
- Pod: 1x A100 SXM 80 GB (RunPod, secure, $1.59/h), 2026-10-05 03:05-03:57 UTC, about $1.40; deleted after the
  download. Plan and price posted on Pagouro issue #2 first. Every picture also upscaled 2x on the pod
  (RealESRGAN_x2plus, `scripts/runpod/upscale2x.py`). Transfer tar hash and all 2,544 file hashes verified.
- Judge: `scripts/showcase_judge.py` (google/gemini-2.5-flash, about $0.85), rubric gained a strict **faces**
  field (none/good/bad), calibrated on x180 before the run (#001 and #107 bad, #073 and #124 good, matching the
  eye). Pick per caption: subject, faces not bad, no lettering, style, appeal, lowest seed. `verdicts.jsonl`,
  `chosen.jsonl`, `judge_summary.txt`.
- Over all 1,272: subject 1,018, lettering 698. Of the 134 picks, **101** passed every check (subject, faces,
  no lettering, poster style).
- **Eye check** of all 101 at contact-sheet size and every picture with a face at 640 px: 12 rejected (reasons in
  `game_picks.json` and `scripts/showcase_jigsaw_b1_to_game.py`). **89 went into the game** as
  `PAGOURO_PLAY/jigsaw/art/be/b1-NNN-slug.jpg`.

## Rights

Outputs of Pagouro BE are CC0, like every BE output.

## Files

Tracked: this README, `captions.jsonl`, `verdicts.jsonl`, `chosen.jsonl`, `judge_summary.txt`, `game_picks.json`,
`SHA256SUMS` (512-px originals), `SHA256SUMS_up` (upscales). Local only (gitignored): `raw/` (1,272 originals +
meta.json), `up/` (1,272 upscales), `b1.tar` (the transfer copy, sha256 87620ab4…f863).
