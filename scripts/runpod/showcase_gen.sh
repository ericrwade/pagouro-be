#!/usr/bin/env bash
# Pagouro BE showcase x180 — pod side. Expects under /workspace/sc: captions.jsonl, showcase_gen.py, upscale2x.py.
# Produces /workspace/sc/raw/*.png (+ meta.json), SHA256SUMS, GEN_DONE in sc.log. The upscale runs later on the chosen list.
set -euo pipefail
cd /workspace/sc
SEEDS="${SEEDS:-1000 1001 1002}"
echo "### setup $(date -u +%FT%TZ)"
python -m pip install -q --break-system-packages "diffusers==0.31.0" "transformers==4.46.3" "accelerate==1.1.1" safetensors pillow huggingface_hub numpy 2>&1 | tail -1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python showcase_gen.py /workspace/sc/captions.jsonl /workspace/sc/raw "$SEEDS"
( cd raw && sha256sum *.png > ../SHA256SUMS )
echo "GEN_ALL_DONE $(date -u +%FT%TZ) $(ls raw/*.png | wc -l) files"
