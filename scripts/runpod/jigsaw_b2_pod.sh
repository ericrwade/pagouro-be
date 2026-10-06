#!/usr/bin/env bash
# Pagouro BE jigsaw batch 2 (2026-10-06), pod side. Expects under /workspace/sc: captions.jsonl, showcase_gen.sh,
# showcase_gen.py, upscale2x.py. Draws 8 seeds per caption (12 for people), upscales every picture 2x, hashes both
# sets and packs b2.tar. Writes progress to /workspace/sc/sc.log and B2_ALL_DONE at the end.
set -euo pipefail
cd /workspace/sc
export SEEDS="1000 1001 1002 1003 1004 1005 1006 1007"
export SEEDS_PEOPLE="1000 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 1011"
bash showcase_gen.sh
echo "### upscale $(date -u +%FT%TZ)"
python upscale2x.py raw up
( cd up && sha256sum *.png > ../SHA256SUMS_up )
tar cf b2.tar raw up SHA256SUMS SHA256SUMS_up
sha256sum b2.tar > b2.tar.sha256
echo "B2_ALL_DONE $(date -u +%FT%TZ) raw $(ls raw/*.png | wc -l) up $(ls up/*.png | wc -l)"
