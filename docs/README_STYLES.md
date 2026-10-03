# Pagouro BE Styles 1.0

Six style plugins for [Pagouro BE](https://github.com/ericrwade/pagouro-be), the Belle Époque image model on a
USB stick. Each is a small LoRA file that rides on the shipped model through stable-diffusion.cpp, so the
model itself does not change and Pagouro BE 1.0 stays exactly what it was. Same rules as everything else in
the project: every training image has a licence you can name and a row in a ledger; the numbers on the box
are measured on a frozen test that ships with it; released once, signed, timestamped.

**The styles:** rock art of the American Southwest (ancient petroglyphs and pictographs, from photographs of
ancestral sites), ukiyo-e woodblock prints, ancient Egyptian tomb painting (from the Met's facsimiles),
Greek vase painting, 19th-century natural-history plates, and 17th-century Dutch oil painting. `STYLES.md`
has, for each one, the corpus and its licences, the gate numbers, and the LoRA weight it ships with.

## Use

Put the `styles` folder inside your Pagouro-BE folder (next to `sd` and `model`), copy
`PAGOURO-BE-STYLE.bat` beside `PAGOURO-BE.bat`, and:

```
PAGOURO-BE-STYLE rockart "a black cat sitting upright"
PAGOURO-BE-STYLE ukiyoe "a lighthouse on a rocky coast at dusk" 20 1234
```

The picture lands in `workspace\art\`. Each style has a trigger phrase the launcher adds for you; with
`sd-cli` directly, use `--lora-model-dir styles` and end the prompt with `<lora:ukiyoe:1.0>` (the weight
`STYLES.md` recommends).

## What it does badly, said plainly

- A style trades subject-following for style. At full weight the rock-art and Greek-vase styles draw the
  style convincingly and lose the subject about half the time or more; the recommended weights are the
  measured compromise. The gate numbers are per style in `STYLES.md`.
- Faces and hands: measured, not promised. On the eight anatomy captions (two eyes, five fingers), no style
  passes more than about half the time, and the plain model does not either. The Dutch style draws the most
  convincing faces to a person; the judge counts fingers strictly.
- Lettering: the rock-art, Greek-vase and Egyptian styles almost never add it; ukiyo-e adds calligraphy to
  most pictures, because the prints have it.

## What is in it

`styles/` the six LoRA files · `ledger/` one training-set ledger per style (source, licence, attribution,
artwork crop, caption as trained) · `evals/` the gate, verdicts, sheets · `styles.json` triggers and
descriptions · `MANIFEST.md` with signature and timestamp proof · `LICENSES.md`.

Captions for every training image were written by an open-weights vision model (Qwen 3.6 27B, Apache 2.0)
and are labelled as such in the ledgers; no commercial API is in this pack's chain.

Eric Wade, with Claude (Anthropic). D-103 in the Pagouro decision ledger.
