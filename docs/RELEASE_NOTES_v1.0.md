# Pagouro BE 1.0

A text-to-image model that draws in the Paris lithographic poster style of 1890–1910, at 512 px, on your CPU,
offline, from a USB stick. The image sibling of [Pagouro](https://github.com/ericrwade/pagouro), built under
the same rules: licensed and ledgered training data, numbers measured on a frozen test that ships with it,
released once, signed, timestamped.

**Not from random weights.** Base: CommonCanvas-S-C (Stable Diffusion 2 architecture, CC-BY-SA-4.0, trained
only on Creative Commons photographs). Our part: 3,043 public-domain posters and prints (Library of Congress,
The Met, Art Institute of Chicago), one ledger row and one labelled machine-written caption each, three
fine-tuning rounds on a rented A100 for $7.72 read from the bill. `CORPUS.md` has the counts.

## The numbers on the box

| | person (40 pictures) | judge (160 pictures) | judge agrees with the person |
|---|---|---|---|
| Subject drawn | **34/40 (85 %)** | 131/160 (82 %) | 34/40 (85 %) |
| Poster style | 36/40 (90 %) | 147/160 (92 %) | 36/40 (90 %) |
| Asked-for words legible | 0/6 | 2/24 | 6/6 |
| Unasked lettering present | — | 136/160 (85 %) | — |

The untuned base draws the subject 62 % of the time under the same rubric. **What it does badly:** it adds
lettering to most pictures whether asked or not, and the lettering is not readable. About 95 seconds per picture on an idle 16-core desktop CPU, run from the
stick; two to three minutes when the machine is busy.

## Download

GitHub caps a release file at 2 GiB and the model alone is 2.58 GB, so this page carries the stick in pieces.
Two ways to get the whole thing:

1. **From this page:** `Pagouro-BE-1.0-win64-kit.zip` (30 MB: runtime, documents, ledgers, evals, manifest,
   signature), plus `pagouro-be-1.0-f16.gguf.part1` and `.part2`, plus `JOIN-MODEL.bat`. Unzip the kit, put
   the two parts and `JOIN-MODEL.bat` inside the `Pagouro-BE` folder, double-click `JOIN-MODEL.bat`: it writes
   `model\pagouro-be-1.0-f16.gguf`, checks its SHA-256
   (`b3a394fc544ca066b83db7f4ae46e77360ccc0e3d454c1d92baa7704e4674708`) and deletes the parts on a match.
2. **One zip:** `Pagouro-BE-1.0-win64.zip` — SHA-256 `f6a059dd4908a29811ac16bd9dc22f89527105b0301965c58d315a9c785d15fc`,
   2,609,894,682 bytes — from https://huggingface.co/Pagouro/pagouro-be-1.0 (and Arweave, if funded).

Either way `VERIFY.bat` must then say *every listed file matches the manifest*. Then, in the folder:

```
PAGOURO-BE "a lighthouse on a rocky coast at dusk"
```

The picture lands in `workspace\art\`. Inside: `sd\` (stable-diffusion.cpp CPU build, MIT), `model\pagouro-be-1.0-f16.gguf`
(2.58 GB; the q8_0 quantisation of this checkpoint draws blank images on CPU, so f16 ships), `ledger\`,
`evals\`, `CORPUS.md`, `facts.json`, `LICENSES.md`, `CHECK_YOUR_COPY.md`, `THREAT_MODEL.md`, `MANIFEST.md`
(67 files) with its minisign signature and `VERIFY.bat` / `verify_manifest.py`.

## Verify your copy

- Manifest SHA-256 `fcbc785dfa55d84f200a532609ea23c551b654db71afe15773cc07461f2b3ec9`; signed with the Pagouro
  key `RWQe8tvI6RCE2uMbuILC9/rEr6bNZdcOA+WC7dHtObLE94ovGk8xuFlG` (`minisign -Vm MANIFEST.md -p pagouro.pub`).
- OpenTimestamps proof `MANIFEST_v1.0.md.ots` (Bitcoin block: pending upgrade at release; filled here when it lands).
- Weights and ledger also at https://huggingface.co/Pagouro/pagouro-be-1.0 (same hashes).

## Licences

Weights CC-BY-SA-4.0 (share-alike inherited from CommonCanvas, with attribution); code Apache 2.0; documents
CC BY-SA 4.0; what it draws for you: CC0, no watermark, no claim.

Eric Wade, with Claude (Anthropic). Frozen at this tag; issues are read, nothing is promised.
