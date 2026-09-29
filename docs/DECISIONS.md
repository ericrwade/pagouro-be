

### D-98 — Pagouro BE: the Belle Époque image model is a sibling release, funded by the RunPod balance
**2026-09-29, Eric: "Definitely a sibling release, perhaps Pagouro_BE (for belle epoque) or Pagouro_Img
whatever you prefer. Spend as much of that runpod credit as you want and as much as you can if it will
improve anything."** Context: Eric asked what it would take to "craft simple Belle Époque images"; the
session first answered from memory ("an entirely new AI") and had to be corrected by the record —
O-21, D-67, D-74, D-75, D-77 already carry a licensed poster corpus, a CommonCanvas LoRA and a 5.5M
on-stick pixel model. None of it reached the D-67 gate before the 1B run took every session; v1.0
shipped text-only and now says so (README, ABOUT, facts.json, site).

**Name:** Pagouro BE (Belle Époque). Repository `ericrwade/pagouro-be`, private through the build
(F3), its own folder `PAGOURO_BE`, its own manifest, signature, timestamp and release. v1.0 of the
text model is frozen and untouched by this.

**What it is, stated without overclaiming (D-50 discipline applies to pictures):** a text-to-image
model that draws in the Paris lithographic poster style of 1890–1910 (D-74), at 512 px, on CPU, offline,
from a USB stick. It is **not from random weights**: the base is CommonCanvas-S-C (Stable Diffusion 2
architecture; weights CC-BY-SA-4.0; trained by Mosaic/Cornell on the CommonCatalog CC-BY + CC-BY-SA
subset of YFCC100M, Flickr images uploaded 2004–2014, with machine-written BLIP-2 captions — every one
of those facts goes in the ledger as the base's row). Our contribution is the corpus and the training
on top of it: public-domain posters and prints, each with a ledger row (source, object id, title,
artist, date, rights statement verbatim, sha256), from the Library of Congress Artist Posters
collection (2,586 items dated 1800–1928, rights "no known restrictions"), The Met Open Access (CC0),
and the Art Institute of Chicago open-access API (CC0, `is_public_domain`). Date basis: every training
image was made before 1929; the base's images before 2015 — so the "before 2022" claim of the text
model holds for the sibling too, and the ledger says on which basis for each part.

**Captions:** the template captions of D-75 ("belleposter, Belle Époque lithograph poster, <title>, by
<artist>, <year>") carry the style but not the content — a title like "Harper's Weekly" teaches nothing
about what is in the picture. Two caption fields per row: (1) the object's own metadata (title, artist,
date, the source's subject headings), and (2) a machine-written description of the picture's content
(one short sentence, written by a vision model through OpenRouter, labelled `caption_source:
"machine (model, date)"` in the ledger exactly as CommonCanvas labels its BLIP-2 captions). Cost stated
before the run: ~4–5k images × one cheap vision call ≈ $2–5.

**Training plan (round 1, ≤ $25):** A100 SXM 80 GB, $1.59/h (secure, LOW stock at the time of writing);
plan + price posted on #2 before create-pod (D-54). Two arms from the same data: (A) full fine-tune of
the UNet at 512 px, bf16, batch 16, ~6–8k steps; (B) LoRA rank 64 as the cheap control. Both generate
the frozen gate set; the pod is deleted before anything is judged.

**Gate (the D-67 gate, made concrete):** 40 frozen captions, written before any training and committed
first — people, animals, objects, places, lettering, and eight that ask for something the era cannot
have (a smartphone, a jet) to see what it does with an impossible request. Four seeds each. Scored by
a fixed rubric (subject recognisable yes/no; in the poster style yes/no; text legible yes/no where text
was asked) by a vision model with a published prompt, and a 40-image sample hand-scored by Eric so the
machine judge's agreement with a person is itself a published number. The baseline is the un-tuned
CommonCanvas-S-C on the same 40, printed beside — the sibling's "comparison line". No bluff-rate
equivalent is claimed; the honest numbers for a picture model are "drew the subject", "in the style",
and "judge agrees with a human".

**Packaging:** stable-diffusion.cpp (CPU build, supports SD2 + GGUF) with the fine-tuned model converted
to GGUF q8_0 (~900 MB), a one-line launcher (`pagouro-be.bat "a woman with a parasol"` → PNG in
`workspace/art/`), README with the same promise structure (licensed, dated, measured, finished,
outputs CC0 per O-28), ledger, MANIFEST, minisign signature (same key), OpenTimestamps, Hugging Face,
GitHub Release, Arweave if Eric funds it. Measured before shipping: seconds per image on the desk CPU
and on Eric's N100 laptop.

**Budget:** the RunPod balance ($127.75 on 2026-09-29, Eric's number) is the ceiling; each pod's
plan and price go on #2 first; round 1 ≤ $25, further rounds only if the gate numbers say they help.
The desk miner may run: training is on RunPod, the desk only fetches, captions and packages.
