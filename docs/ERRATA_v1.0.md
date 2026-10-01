# Errata — Pagouro BE 1.0

*Shipped bytes are not changed; these are the rough edges and the way round each.*

| # | What | Way round |
|---|---|---|
| E1 | The signed kit's `ledger/` holds every source ledger but not the final selection-and-crop ledger the packager meant to copy (`training_set.jsonl`); the round-3 set was built without writing one. Found by an outside review, 2026-10-01. | `ledger/training_set_r3.jsonl` on Hugging Face (`Pagouro/pagouro-be-1.0`) and `docs/ledger/` in the repository: 3,270 rows, one per training file, with the source row, crop box, and the caption as trained. |
| E2 | The model card did not say that CommonCanvas-S-C's text encoder (OpenCLIP, trained on LAION captions) and VAE (Stable Diffusion 2) are inherited unchanged and are not covered by the CC image set or the museum ledger. | Stated in the card, `CORPUS.md` and `facts.json` since 2026-10-01. |
| E3 | The q8_0 quantisation of the shipped checkpoint draws blank images on CPU (cause undiagnosed); the f16 file ships. | Use the f16 GGUF or the fp16 safetensors. |
