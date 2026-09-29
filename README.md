# Pagouro BE

*Belle Époque. A text-to-image model that draws in the Paris lithographic poster style of
1890–1910, at 512 px, on your CPU, offline, from a USB stick. A sibling of
[Pagouro](https://github.com/ericrwade/pagouro), the 1B text model, built under the same rules and
the same discipline: every training image has a licence you can name and a row in a ledger; the
numbers on the box are measured on a frozen test that ships with it; released once, signed,
hash-anchored, mirrored. Private through the build (F3); this README is being written as the
thing is made and says so where a number is not yet measured.*

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

## Status

Build in progress (D-98, 2026-09-29). Round 1 trains on one rented A100; the gate numbers, the
model file and the packaging follow. Numbers marked TBD are not yet measured.

| Field | Value |
|---|---|
| Base | CommonCanvas-S-C, CC-BY-SA-4.0, SD2 architecture, 512 px |
| Our corpus | TBD images (LoC / Met / AIC), all pre-1929, `docs/CORPUS.md` |
| Training | TBD steps full UNet fine-tune, 1× A100 80 GB, bf16; LoRA control arm |
| Gate | 40 captions × 4 seeds; subject / style / lettering, judge + human sample |
| Runs on | any 64-bit CPU via stable-diffusion.cpp (GGUF q8_0); seconds per image TBD |
| Licences | model weights CC-BY-SA-4.0 (share-alike inherited from the base); code Apache 2.0; outputs CC0 |
| Made by | Eric Wade, with Claude (Anthropic) |
