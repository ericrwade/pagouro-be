# Licences (Pagouro BE Styles)

- **The LoRA files** (`styles/*.safetensors`): CC BY-SA 4.0. They are derivatives of the Pagouro BE weights,
  which are themselves CC BY-SA 4.0 as a fine-tune of CommonCanvas-S-C (CC BY-SA 4.0); the share-alike
  travels with them. Attribution: "Pagouro BE Styles, Eric Wade with Claude (Anthropic), 2026; on Pagouro BE
  and CommonCanvas-S-C."
- **Training images**, per style, each row in `ledger/<style>.jsonl` with the licence as found:
  - *Rock art*: photographs from Wikimedia Commons under CC0, public domain, CC BY or CC BY-SA, each with the
    photographer's attribution line in the ledger (`artist`, `credit`, `attribution`, `license`, `license_url`).
    Those attributions are part of this pack; keep the ledger with the files. The sites photographed are
    ancestral Indigenous places; the pack names the sources and makes no claim to the cultures' meanings.
  - *Ukiyo-e*: Cleveland Museum of Art (CC0) and Art Institute of Chicago (CC0, public domain).
  - *Egyptian*: the Metropolitan Museum's facsimiles (CC0) as uploaded to Wikimedia Commons, plus Commons
    photographs under the licences listed per row.
  - *Greek vase*: Wikimedia Commons photographs (licences per row, attributed) and Cleveland (CC0).
  - *Natural history*: public-domain plates (Audubon, Haeckel and others) from Wikimedia Commons.
  - *Dutch*: public-domain paintings from Wikimedia Commons and Cleveland (CC0).
- **Captions**: written by Qwen 3.6 27B (open weights, Apache 2.0) through OpenRouter, labelled per row.
- **Scripts and documents**: Apache 2.0 (code), CC BY-SA 4.0 (documents).
- **What it draws for you**: CC0. No watermark; the project claims no rights in the pictures.
