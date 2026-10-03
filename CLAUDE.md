# PAGOURO BE — project operating rules

This file auto-loads whenever a session touches `C:\Users\Eric Wade\PAGOURO_BE`. Pagouro BE is the image
sibling of Pagouro; the rules of `C:\Users\Eric Wade\PAGOURO_BUILD\CLAUDE.md` apply here unchanged
(secrets never in the transcript; `.env` lives in PAGOURO_BUILD and is read by path; cost is real; decisions
are logged; provenance is the product; the build log keeps the mistakes).

## Start of every session — in this order

1. `C:\Users\Eric Wade\PAGOURO_BUILD\docs\HANDOFF_2026-10-01.md` — the cold-start page for both models.
2. `README.md` here — what the model is, said plainly, with the box numbers.
3. `docs/DECISIONS.md` here (D-98, D-99, D-100) — why it is what it is; the full ledger is in PAGOURO_BUILD.
4. `docs/FLIP.md`, `docs/RELEASE_NOTES_v1.0.md`, `docs/facts.json` — what shipped, with hashes.

## State (2026-10-01)

Released 2026-09-29, version 1.0, frozen. Repo public (not archived), release v1.0 published, Hugging Face
`Pagouro/pagouro-be-1.0` public, manifest `fcbc785d…` signed with the Pagouro key and attested in Bitcoin
block 969239, mirror at https://pagouro.qstorage.quilibrium.com/ . Shipped bytes: `release/Pagouro-BE-1.0/`
(67 files) and `release/dist/` (one zip `f6a059dd…`, kit, model parts). Local stick `D:\Pagouro-BE`.
Nothing runs, nothing is rented. Every box number is measured (N100: 52 min per picture, 2026-10-01).

**Styles pack (D-103, 2026-10-02): built, not released.** `release/Pagouro-BE-Styles-1.0/` (six LoRAs, manifest
`9b0a5a72…`) waits for Eric's minisign signature; then ots (`manifest` input), release `styles-1.0`, HF, mirror.
LoRAs ship as original-SD names + alpha (`scripts/convert_lora_kohya.py --ldm`); draw only at 512x512 with
DPM++ 2M (see the D-103 runtime paragraph). Rebuild: `scripts/package_styles.py --version 1.0 --weights
rockart=0.6,greekvase=0.6,naturalhistory=0.8,egyptian=0.8,ukiyoe=1.0,dutch=1.0`.

## Layout

`scripts/` — corpus fetchers (LoC, AIC, Met), captioning, training-set builders, pod scripts
(`runpod/be_train.sh`, `be_train2.sh`, launchers), judge (`judge_gate.py`, rubric v2), human-scoring flow
(`make_human_sample.py` → `make_scoring_page.py` → Artifact → `score_human.py`), packager, zip/split, HF
upload, QStorage mirror, desktop launcher (`Draw-PagouroBE.ps1`). `evals/` — the frozen gate and every
round's verdicts and human samples. `showcase/` — twelve gate pictures with verdicts. `docs/` — decisions,
corpus, model card, release notes, flip order, facts, signed manifest + proof + key. `site/` — the mirror's
link page and the drag-and-drop folder. Data (images, ledgers) lives in `PAGOURO_BUILD/data/images/` and
is not in any repo; `runs/`, `tools/`, `release/` are gitignored.

## Hard rules specific to this folder

- The signed folder `release/Pagouro-BE-1.0/` and everything in `release/dist/` are shipped bytes: never edit.
- Any new training is a new decision (D-101+), a posted plan and price on Pagouro issue #2, Eric's word
  for the pod, and a new version number — never an overwrite of 1.0.
- Numbers come from `docs/facts.json` and `evals/`, never from recollection.
