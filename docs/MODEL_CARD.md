---
license: cc-by-sa-4.0
base_model: common-canvas/CommonCanvas-S-C
tags:
- text-to-image
- stable-diffusion
- gguf
- poster
- belle-epoque
- public-domain-training-data
language:
- en
---

# Pagouro BE 1.0

A text-to-image model that draws in the Paris lithographic poster style of 1890–1910, at 512 px, on a CPU,
offline. A sibling of [Pagouro](https://huggingface.co/Pagouro/pagouro-1.0), built under the same rules:
every training image has a licence you can name and a row in a ledger; the numbers on the box are measured
on a frozen test that ships with it; released once, signed, timestamped.

**Not from random weights.** The base is [CommonCanvas-S-C](https://huggingface.co/common-canvas/CommonCanvas-S-C)
(Stable Diffusion 2 architecture, CC-BY-SA-4.0, trained by its authors only on Creative Commons photographs
with machine-written captions). Our part is the corpus and the fine-tune on top: 3,043 public-domain posters
and prints (Library of Congress *Artist Posters*, The Met Open Access, Art Institute of Chicago), each with
its own ledger row and a one-sentence content caption written by a vision model (Google Gemini 2.5 Flash-Lite,
through OpenRouter, 2026-09-29) and labelled as such in the ledger. Those captions are the one training input not
under a public licence: they are API outputs, and Google's Gemini API terms restrict using outputs to develop
models that compete with Google. Our reading is that a poster-style fine-tune of a Creative-Commons diffusion
model is not such a model; the reader can judge, and a future version can re-caption with an open-weights
vision model and retrain. The images themselves are public domain.
Everything in our part was made before 1929; the base's photographs were uploaded before 2015. Two inherited
components are not covered by either ledger: the OpenCLIP text encoder (trained on LAION captions, per the
CommonCanvas paper) and the Stable Diffusion 2 VAE. Our fine-tune changed the UNet only.

## Post-publication note (2026-10-01)

Two days after release, two independent audits of the Pagouro project (one by Grok, one by ChatGPT, both
asked "is it as FOSS as they claim?") found things we had stated too strongly or left out. We want you to
know what they found and what changed. Nothing that shipped was altered; the record was corrected around it.

- The model card did not name the model that wrote the training captions. It was Gemini 2.5 Flash-Lite
  through OpenRouter; Google's API terms restrict using outputs to develop competing models, and our reading
  is that a poster fine-tune of a Creative-Commons diffusion model is not one. The captions are the one
  training input without a public licence, and a future version can re-caption with an open-weights model.
- CommonCanvas-S-C's text encoder (OpenCLIP, trained on LAION captions) and its Stable Diffusion 2 VAE are
  inherited unchanged; they are not covered by the museum ledger or CommonCanvas's CC image set (erratum E2).
- The final selection-and-crop ledger was missing from the signed kit by a packaging slip; it is on Hugging
  Face and in the repository as `ledger/training_set_r3.jsonl` (erratum E1).

**Follow-up (2026-10-02).** Both auditors re-ran their checks after the changes and upgraded their assessments.
What they found has been fixed to the extent it can be. What remains is recorded as a limit rather than a
fix: the pretraining volume's per-shard metadata was deleted with the rented pod; the web crawl's licence
covers the dataset, not each page; and Pagouro BE's captions came from a commercial API. A future version is
the honest path for those, never an edit of 1.0.

The full record is O-49 and D-102 in `docs/DECISIONS.md`, and `docs/ERRATA_v1.0.md`.

## What it draws

![twelve gate pictures](showcase/sheet.jpg)

Twelve pictures from the model's own gate run, chosen by hand and not retouched; captions, seeds and the judge's verdicts in `showcase/README.md`. The last is a lettering failure kept on purpose.

## The numbers on the box

Measured on the frozen 40-caption gate (`evals/gate40.jsonl`, committed before any training), 4 seeds each,
judged blind by a vision model with a fixed strict rubric, plus 40 pictures scored by a person.

| | person (40 pictures) | judge (160 pictures) | judge agrees with the person |
|---|---|---|---|
| Subject drawn | **34/40 (85 %)** | 131/160 (82 %) | 34/40 (85 %) |
| Poster style | 36/40 (90 %) | 147/160 (92 %) | 36/40 (90 %) |
| Asked-for words legible | 0/6 | 2/24 | 6/6 |
| Unasked lettering present | — | 136/160 (85 %) | — |

The untuned base scores 62 % on subject under the same rubric. **What it does badly:** it adds lettering to
most pictures whether asked or not, and the lettering is not readable. It is not a frontier image model. It
takes no image input and writes no text.

## Files

| file | what |
|---|---|
| `pagouro-be-1.0-f16.gguf` | the model for stable-diffusion.cpp (f16; the q8_0 quantisation of this checkpoint draws blank images on CPU, so f16 ships) |
| `pagouro-be-1.0-fp16.safetensors` | the same weights, single-file SD2 layout, for diffusers / other loaders |
| `MANIFEST.md`, `.minisig`, `.ots`, `pagouro.pub` | the stick manifest (67 files), its minisign signature (key `RWQe8tvI…`, the Pagouro key), its OpenTimestamps proof (Bitcoin block 969239) |
| `ledger/` | every source ledger with captions; `ledger/training_set_r3.jsonl` is the final selection-and-crop ledger (3,270 rows), added 2026-10-01 after an outside review found it missing from the signed kit |
| `evals/` | the gate, verdicts, judge summaries, the human samples |
| `CORPUS.md`, `facts.json` | sources, counts, licences; key facts in one JSON |

## Use

With [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) (CPU build):

```
sd-cli -m pagouro-be-1.0-f16.gguf -p "belleposter, Belle Epoque lithograph poster, a black cat sitting upright" \
  -n "photograph, photo, realistic, 3d render, blurry, watermark, modern, gradient" --steps 20 --cfg-scale 7 -W 512 -H 512 -o cat.png
```

Keep the prefix `belleposter, Belle Epoque lithograph poster,` — it is the trigger the corpus was captioned
with. About 95 s per picture on an idle 16-core desktop CPU; about 52 minutes on an Intel N100 laptop (measured, from the stick). With diffusers, load the `.safetensors` UNet into
the CommonCanvas-S-C pipeline (the SD2 configs on the Hub are gated; CommonCanvas ships its own).

## Licences

Weights CC-BY-SA-4.0 (share-alike inherited from CommonCanvas; attribution to its authors and to this
fine-tune). Training images public domain, per row in `ledger/`. Outputs CC0; no watermark; no claim on what
it draws for you.

**Made by** Eric Wade, with Claude (Anthropic). Repository: https://github.com/ericrwade/pagouro-be.
