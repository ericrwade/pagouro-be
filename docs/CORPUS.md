# Pagouro BE corpus (round 1, built 2026-09-29)

Every image below has a row in a ledger with its source, object id, title, artist, date, the rights
statement as found, the image URL, SHA-256 and pixel size. The ledgers live beside the images in
`PAGOURO_BUILD/data/images/{loc,aic}/ledger.jsonl` and `met_curated.jsonl`; the training-set ledger
(`be_train/ledger.jsonl`) records, per training file, which source row it came from, the crop box, the
assembled caption and the SHA-256 of the 512-px file. Numbers here are read from those files.

## The base model (not ours; its row)

| Field | Value |
|---|---|
| Model | CommonCanvas-S-C, `common-canvas/CommonCanvas-S-C` on Hugging Face |
| Architecture | Stable Diffusion 2 (UNet 865.9 M params, OpenCLIP text encoder 340.4 M), 512 px, epsilon prediction |
| Weights licence | CC-BY-SA-4.0 (so our fine-tune is CC-BY-SA-4.0 too, with attribution) |
| Training data | CommonCatalog, the CC-BY + CC-BY-SA subset of YFCC100M (Flickr, uploads 2004–2014); captions machine-written (BLIP-2) by its authors |
| Paper | arXiv 2310.16825 |
| Inherited components | CommonCanvas-S-C is not only its UNet: per its paper the text encoder is OpenCLIP (trained on LAION captions, not a CC-only set) and the VAE is Stable Diffusion 2's. Our fine-tune changed the UNet only; the text encoder and VAE ship as inherited, and their training history is not covered by the museum ledger or CommonCanvas's CC image set. |
| Note | Its model card's own heading reads "CommonCanvas-S-NC" on the S-C repository; the licence file and dataset tags say S-C (commercial subset). Recorded as found. |

## Our corpus

| Source | Images | Licence / rights basis | Query |
|---|---|---|---|
| Library of Congress, *Artist Posters* | 1,411 | "No known restrictions on publication" per item, and published before 1929 (US public domain) | collection walk, dates 1880–1928 (a wider 1800–1928 walk is running for round 2) |
| The Met Open Access | 533 | CC0 (`isPublicDomain=true`), curated for the D-75 LoRA (prints and plates; poster masters) | poster-master and print-world queries, D-67 |
| Art Institute of Chicago | 865 | CC0 (`is_public_domain=true`), dated 1860–1928 | `medium_display` matches "lithograph", date_start 1860–1928 |
| **Total** | **2,809** unique images | all made before 1929 (dated rows 1516–1928; 2,621 of 2,809 carry a year) | |

Training files: **3,969** at 512 px — the centre square of every image (2,805) plus the top square
of every tall image (1,164), where the lettering usually is. 212 faint crops (grey-level std < 18)
were dropped.

Top artists by image count: Toulouse-Lautrec 365, Redon 174, Fantin-Latour 62, Penfield 52, Munch 44,
Steinlen 41, Brill 39; 401 rows have no named artist; 171 LoC rows carry the Rehse Archiv as
contributor (German posters of 1914–1918). The corpus is broader than the Paris poster of 1890–1910
that the style brief names (D-74): it includes British and American posters, First World War posters,
Redon's and Fantin-Latour's tonal lithographs, and the Met's trade cards and natural-history plates.
The trigger word and the caption prefix carry the style; the content caption carries the picture.

**What it also learned (noticed 2026-10-01).** Some pictures come out as a photograph of a poster rather than
the poster itself: a black border, a mount, and on the left edge the colour-calibration strip that archive
scanners place beside an object. The Library of Congress and museum images are scans of physical sheets, and
the model learned the scanning as part of the style. A future version can crop the strips out of the corpus;
this one draws them sometimes, and the lighthouse drawn on an N100 laptop is an example (`showcase/`).

## Captions

Each training caption is assembled as

    belleposter, Belle Époque lithograph poster, <content caption>, by <artist>, <year>

where `<content caption>` is one sentence describing the picture, written by `google/gemini-2.5-flash-lite`
through OpenRouter on 2026-09-29 (2,808 of 2,809 images; one Met row fell back to its title). The
ledger labels every such caption `caption_source: "machine (google/gemini-2.5-flash-lite, 2026-09-29)"`.
Cost: 2,809 calls, ≈ 3.8 M prompt tokens, ≈ 60 k completion tokens, about $0.45.

**Terms note (added 2026-10-01 after an outside review).** The content captions are outputs of a commercial API
(Gemini 2.5 Flash-Lite via OpenRouter). Google's Gemini API terms restrict using outputs to develop models that
compete with Google; our reading is that this poster fine-tune is not one, but the captions are the single training
input without a public licence, and the ledger says so per row (`caption_source`). A future version can replace them
with captions from an open-weights vision model (e.g. Qwen2.5-VL, Apache 2.0) and retrain.

## What is not in it

No web-scraped images, no images without a rights statement, nothing dated after 1928 in our part,
nothing from the base's data that its authors did not license. Gallica (BnF) was left out because its
reuse terms distinguish commercial from non-commercial use; Wikimedia Commons because licence status
there is per file and would need a per-file check we did not do.
