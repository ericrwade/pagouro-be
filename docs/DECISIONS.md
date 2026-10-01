

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


### D-99 — Pagouro BE round 1 read: the fine-tune draws the subject, the lettering is glyph salad, the judge is lenient; round 2 plan
**2026-09-29, from the measured files (`evals/results/round1/`).** Pod `p4jminvdkm9q0a`, A100 SXM 80 GB,
$1.61 read from the billing API, 1 h 37 min create-to-delete. Corpus 2,809 licensed images → 3,969 crops
(`docs/CORPUS.md`). Arms: full UNet fine-tune 5,000 steps bs16 bf16 (64 min); LoRA r64 2,000 steps
(10 min). Gate 40 × 4 seeds × {base, ft, lora}, judge gemini-2.5-flash, arm-blind.

**Numbers.** Judge, subject recognisable: base 125/160 (78 %), **ft 143/160 (89 %)**, lora 141/160 (88 %).
Style: 94 / 97 / 99 %. Words legible: 0/24, 0/24, 1/24. Human (Eric, 40 blind): subject base 9/12,
**ft 11/16 (69 %)**, lora 8/12; style 40/40; words 0/6. Judge–human agreement: subject 33/40 (82 %),
style 38/40 (95 %), words 6/6. Six of seven subject disagreements are judge-yes/human-no, four on
lettering captions where the judge accepted "a poster with lettering" as the subject.

**Reads.** (1) The fine-tune adds about eleven points of subject-following over the base by the judge;
by the human the sample is too small to rank ft against lora, and both sit near 70 %. (2) Style is
saturated for every arm including the untuned base — the prompt prefix alone makes posters — so the
style question separates nothing and comes off the headline. (3) Lettering is the failure: asked-for
words never come out legible, and (Eric's note) unasked jumbled lettering appears in most pictures,
because the corpus is posters and posters have words. The CPU test image (a black cat) grew a title
and a caption line on its own. (4) The judge is lenient on subject; the human number is the box number
and the judge's agreement rate is printed beside it (D-50 discipline for pictures). (5) The GGUF q8_0
path works: stable-diffusion.cpp converts the fp16 SD2 checkpoint in 3 s to a 2.03 GB file and draws a
correct picture on CPU; timing is unmeasured until the desk miner is paused (641 s with it running).

**Round 2 (≤ $10, same pod class).**
- Corpus: add the wider LoC walk (1800–1928; at 2,096 of 2,586 seen it had added 100 posters) with
  content captions for the new rows only.
- Captions: images whose content caption quotes no lettering get ", no lettering" appended; images with
  lettering keep the quoted words. Teaches the absence as well as the presence.
- Training: full fine-tune only (LoRA was the control and matched it), 8,000 steps from the round-1
  weights (fp16 single file reloaded), same data + the lettering suffix.
- Decode: gate generated twice for the ft arm — plain, and with a lettering negative prompt
  ("text, lettering, letters, words, writing, caption") for captions that ask for no words.
- Gate rubric v2: subject for lettering captions requires the asked word; style dropped from the
  headline (kept in the file); new item **unasked lettering present** (yes/no) for every picture;
  human sample 40 again, blind, same page.
- Box numbers (planned): *subject drawn* (human rate, judge rate, agreement), *unasked lettering*
  rate, *asked words legible* rate, seconds per image on the desk CPU and on the N100.


### D-100 — Pagouro BE: round 3 is the shipping candidate; f16 ships because q8_0 draws blanks; the box numbers
**2026-09-29, from the measured files (`evals/results/round{2,3}/`, `docs/facts.json`).** Three rounds on one
A100 each, $7.72 for the day read from the billing API, every pod deleted (`list-pods` []).

**Round 2** (D-99 plan: ", no lettering" suffix on 538 of 4,120 captions, 8,000 steps from round 1): strict
subject 76 %, unasked lettering 89 % plain / 81 % with a lettering negative prompt, words 0/24 — the suffix
was too rare to move the prior, the negative prompt costs subject. **Round 3** (centre crops only — the
top-square title bands dropped — lettering-free images ×2, 3,270 files, 4,000 steps from round 2): strict
subject **82 %** (131/160), style 92 %, unasked lettering **85 %** (136/160), asked words legible 2/24; the
negative prompt no longer helps (85 %) and costs subject (79 %), so the plain decode is the candidate.
Untuned base on the same strict rubric: 62 %.

**Packaging finding.** stable-diffusion.cpp's q8_0 quantisation of the round-3 checkpoint produces a flat
brown square on CPU, reproducibly (two conversions, two prompts), while the round-1 q8_0 drew correctly and
the round-3 fp16 file and its f16 GGUF draw correctly (`evals/results/round3/cpu_cat_*`). Cause not
diagnosed (weights are healthy: identical tensor set and shapes to round 1, no NaN in the loss); the f16
GGUF (2,580,023,872 bytes) ships and the fact is recorded on the box. The stick (`release/Pagouro-BE-1.0/`,
63 files, 2.64 GB) verifies against its manifest; the one-line launcher draws a lighthouse from a cold
start. Timing on the desk (AMD Ryzen AI MAX+ 395, 16 cores, a miner intermittently active): 107, 95, 197 s
per 512-px image at 20 steps. The N100 number is Eric's to measure.

**Box numbers (D-50 for pictures):** *subject drawn* — human rate from Eric's 40-image blind score (pending),
judge rate 82 %, judge–human agreement printed beside it; *unasked lettering* 85 %; *asked words legible*
2 of 24; seconds per image. The lettering line is stated as a limitation, not hidden: it draws words on most
pictures and they are not readable.

**Left before public:** Eric's second score → final numbers into README/facts → repackage → Eric signs the
manifest with the Pagouro key → OpenTimestamps → Hugging Face `Pagouro/pagouro-be-1.0` + GitHub Release on
`ericrwade/pagouro-be` (repo flips public with it; Arweave only if Eric funds it) → one line on pagouro.com.
Further training rounds: none unless Eric asks; the remaining lever is a lettering-free-majority corpus
(masked title bands), ≈ $3 a round.

**Human score in (2026-09-29, later):** 40 pictures from the shipped model, one per caption, scored by Eric: subject drawn 34/40 (85 %), style 36/40 (90 %), asked words legible 0/6. Judge–human agreement on subject 34/40 (85 %), style 90 %, words 6/6; the six disagreements split four human-yes/judge-no (lettering captions, where the strict judge wants the word itself) and two the other way. Box: **subject drawn 85 % (person) / 82 % (judge), agreement 85 %; unasked lettering 85 %; asked words legible 0 of 6 (person) / 2 of 24 (judge)**.


### O-49 — First outside review (Grok, expert mode, 2026-10-01) and what changed because of it
**Eric pasted the review.** Verdict: "a copyleft open release with a documented ledger, not a marketing open-weights tag"; the from-scratch claim, the ledger, the integrity chain and BE's honesty about its base all held. Four soft spots, each answered the same day: (1) the mirror page said "everything is free and open source" while D-64 reserves the story chapters — the sentence now lists the licences by part; (2) the llama.cpp MIT notice does not travel with the stick's binaries — erratum E5, the text is in `licenses/` and the release notes; (3) BE's model card did not name the caption model — it now names Gemini 2.5 Flash-Lite via OpenRouter and records that Google's API terms restrict outputs used to develop competing models, with our reading and the open-weights re-caption path for a future version; (4) the corpus is a ledger plus fetch scripts, not bundled bytes, and FineWeb-Edu's ODC-By is a dataset licence, not a grant from every page author — already stated in the README and the brief, left as is. No shipped byte changed.


### D-102 — Second outside review (ChatGPT, 2026-10-01) and what changed because of it
**Eric pasted the review; it ran while the O-49 changes were in progress.** Its verdict: the software is FOSS and the weights carry real freedoms; the stronger claim of a fully licensed, fully reconstructible system was not supported. Checked against the files and answered the same day, no shipped byte changed: (1) "every training byte has a licence" overstated ODC-By, which licenses the FineWeb-Edu dataset, not each page — README, ABOUT, model card, site, facts and the Alexis bible now say "every training source" and state the scope; (2) the SFT set includes 5,184 conversations generated by Qwen2.5-7B-Instruct and 30 by DeepSeek-R1-Distill-Qwen-7B (both in `corpus.json`) — now disclosed as output-based distillation of chat behaviour, with the pre-2022 basis scoped to pretraining; (3) only the q8_0/q4_k_m GGUFs were published — the shipped model and the base are now on Hugging Face at f32 (GGUF) and as PyTorch checkpoints, with the 32,768-entry tokenizer the run used (the Flash tokenizer was uploaded first by mistake and replaced the same hour) and the volume files; the tokenized volume's per-shard metadata was deleted with the pod and is recorded as not published; (4) BE's final selection-and-crop ledger was missing from the signed kit — `ledger/training_set_r3.jsonl` (3,270 rows) is on Hugging Face and in the repo, BE erratum E1; (5) CommonCanvas's inherited OpenCLIP text encoder (LAION captions) and SD2 VAE were not disclosed — now in BE's card, CORPUS and facts, erratum E2; (6) the llama.cpp notice (E5) and the story chapters (D-101) were already being fixed when the review ran. Not done: a fully libre re-caption of BE and a FineWeb-free text corpus are new versions, not edits.
