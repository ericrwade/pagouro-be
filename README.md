# Pagouro BE

*Belle Époque. A text-to-image model that draws in the Paris lithographic poster style of
1890–1910, at 512 px, on your CPU, offline, from a USB stick. A sibling of
[Pagouro](https://github.com/ericrwade/pagouro), the 1B text model, built under the same rules and
the same discipline: every training image has a licence you can name and a row in a ledger; the
numbers on the box are measured on a frozen test that ships with it; released once, signed,
hash-anchored, mirrored. Public since 2026-09-29.*

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

The full record is O-49 and D-102 in `docs/DECISIONS.md`, and `docs/ERRATA_v1.0.md`.

## What it is, said plainly

- **Not from random weights.** The base is CommonCanvas-S-C (Stable Diffusion 2 architecture,
  weights CC-BY-SA-4.0), trained by its authors only on Creative Commons images (the CC-BY and
  CC-BY-SA subset of YFCC100M, Flickr photographs uploaded 2004–2014) with machine-written
  captions. That is why it was chosen: it is the one text-to-image base whose training data has
  a licence statement that survives inspection. Its row is in the ledger like any other source.
- **Our part is the corpus and the training on top.** Public-domain posters and prints, each with
  its own ledger row — source, object id, title, artist, date, rights statement as found, SHA-256:
  the Library of Congress *Artist Posters* collection (dated 1800–1928, "no known restrictions"),
  The Met Open Access (CC0), the Art Institute of Chicago open-access API (CC0, `is_public_domain`).
  `docs/CORPUS.md` has the counts and the queries.
- **Dated.** Every poster in the corpus was made before 1929. The base's photographs were uploaded
  before 2015. Nothing after 2022 anywhere, and the ledger says on which basis for each part.
- **Captions.** Each image carries two: its own record (title, artist, date, subjects) and a
  one-sentence description of what is in the picture, written by a vision model and labelled as
  machine-written in the ledger — the same labelling CommonCanvas gives its captions.
- **Measured, then frozen.** A 40-caption gate (`evals/gate40.jsonl`), committed before any
  training: people, animals, objects, places, lettering, and eight things the era could not have
  drawn. Scored by a fixed rubric (subject recognisable, in the poster style, lettering legible)
  by a vision model with a published prompt, with a sample hand-scored by a person so the judge's
  agreement with a human is itself a published number. The untuned base on the same 40 is the
  comparison line. No picture model has a "bluff rate"; these three numbers are the honest
  equivalent and they are the ones on the box.
- **Text only in, picture out.** It draws. It does not read images, write text, or run tools.
  Lettering inside pictures is drawn, not typed, and is often wrong; the gate measures how often.
- **Yours.** Outputs are CC0 (O-28). No watermark. Nothing you type leaves the machine;
  `docs/THREAT_MODEL.md` (inherited from Pagouro) says exactly what that covers.

## What it draws

![twelve gate pictures](showcase/sheet.jpg)

Twelve pictures from the model's own gate run, chosen by hand, not retouched, with the judge's verdict on each: `showcase/README.md`. The last one is a lettering failure kept on purpose.

## Status

**Released 2026-09-29, version 1.0, frozen.** Download: https://github.com/ericrwade/pagouro-be/releases/tag/v1.0 (kit + model parts; the one-zip stick, SHA-256 `f6a059dd…`, is on Hugging Face) · weights and ledger: https://huggingface.co/Pagouro/pagouro-be-1.0 · manifest SHA-256 `fcbc785d…`, signed with the Pagouro key, timestamped on Bitcoin block 969239 (OpenTimestamps). Mirror with the receipts: https://pagouro.qstorage.quilibrium.com/ . On an Intel N100 laptop, from the stick: about 52 minutes per picture (measured 2026-10-01), so the box says "minutes on a desktop, most of an hour on a cheap laptop".

| Field | Value |
|---|---|
| Base | CommonCanvas-S-C, CC-BY-SA-4.0, SD2 architecture, 512 px |
| Our corpus | 3,043 images (LoC 1,515 / Met 533 / AIC 995), all pre-1929, `docs/CORPUS.md` |
| Training | three rounds, 17,000 steps of full UNet fine-tune in all, 1× A100 80 GB, bf16, $7.72 read from the bill; round 3 ships (centre crops, lettering-free images ×2) |
| Gate (judge, strict rubric) | subject drawn 131/160 (82 %); untuned base 62 %; unasked lettering 136/160 (85 %); asked words legible 2/24 |
| Gate (human) | 40 pictures from the shipped model, one per caption, scored by a person: subject drawn 34/40 (85 %), poster style 36/40 (90 %), asked words legible 0/6; the judge agrees with the person on subject 34/40 (85 %) |
| Runs on | any 64-bit Windows CPU via stable-diffusion.cpp, f16 GGUF (2.58 GB; the q8_0 quantisation of this checkpoint draws blanks, so f16 ships); 95 s per 512-px image at 20 steps from the USB stick on an idle 16-core desktop (95–197 s with a miner active on the same machine); 3,099 s (52 min) on an Intel N100 laptop from the stick, plus 103 s to load the model |
| Licences | model weights CC-BY-SA-4.0 (share-alike inherited from the base); code Apache 2.0; outputs CC0 |
| Made by | Eric Wade, with Claude (Anthropic) |
