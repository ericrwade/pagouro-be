# Pagouro BE — the flip (on Eric's word "flip")

In order, nothing before the word; each step reversible except the last two are not worth reversing.

1. Hugging Face `Pagouro/pagouro-be-1.0` → public (`update_repo_settings(private=False)`).
2. GitHub release `v1.0` on `ericrwade/pagouro-be` → body from `docs/RELEASE_NOTES_v1.0.md`, `--draft=false --latest`.
3. Repository `ericrwade/pagouro-be` → public (not archived: issues stay open, as for Pagouro).
4. pagouro.com: one section for BE (links, the three hashes, the box numbers) — `docs/site/index.html` in
   PAGOURO_BUILD and the site repo.
5. `docs/ALEXIS_BIBLE.md` in PAGOURO_BUILD: a facts row and two approved posts for BE (numbers from facts.json).
6. #2: the release post; memory note; session log; BUILD_LOG entry ("Day 21 — the sibling").
7. When the OTS upgrade lands: block height into facts.json, README, release notes, HF; re-upload `.ots` to
   HF and the release assets (the manifest itself does not change, so no re-signing).
8. Arweave: only if Eric funds it (≈ $110 at the September rate for 2.6 GB). QStorage: when writes work.

Numbers that go out with the flip (from `docs/facts.json`): subject drawn 85 % (person) / 82 % (judge),
judge–human agreement 85 %; unasked lettering 85 %; asked words legible 0/6; untuned base 62 %;
95–197 s per picture on a 16-core desktop; $7.72 of GPU.
