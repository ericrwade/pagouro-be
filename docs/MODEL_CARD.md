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
its own ledger row and a one-sentence content caption written by a vision model and labelled as such.
Everything in our part was made before 1929; the base's photographs were uploaded before 2015.

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
| `ledger/` | the training-set ledger and every source ledger with captions |
| `evals/` | the gate, verdicts, judge summaries, the human samples |
| `CORPUS.md`, `facts.json` | sources, counts, licences; key facts in one JSON |

## Use

With [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) (CPU build):

```
sd-cli -m pagouro-be-1.0-f16.gguf -p "belleposter, Belle Epoque lithograph poster, a black cat sitting upright" \
  -n "photograph, photo, realistic, 3d render, blurry, watermark, modern, gradient" --steps 20 --cfg-scale 7 -W 512 -H 512 -o cat.png
```

Keep the prefix `belleposter, Belle Epoque lithograph poster,` — it is the trigger the corpus was captioned
with. About 100–200 s per picture on a 16-core desktop CPU. With diffusers, load the `.safetensors` UNet into
the CommonCanvas-S-C pipeline (the SD2 configs on the Hub are gated; CommonCanvas ships its own).

## Licences

Weights CC-BY-SA-4.0 (share-alike inherited from CommonCanvas; attribution to its authors and to this
fine-tune). Training images public domain, per row in `ledger/`. Outputs CC0; no watermark; no claim on what
it draws for you.

**Made by** Eric Wade, with Claude (Anthropic). Repository: https://github.com/ericrwade/pagouro-be.
