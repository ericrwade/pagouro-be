#!/usr/bin/env bash
# Pagouro BE Styles (D-103) on one A100. Expects under /workspace/st:
#   r1/pagouro-be-r3-fp16.safetensors     the shipped BE model (single-file SD2); start point for every LoRA
#   styles.json, gate40_styles.jsonl
#   train/<style>/512/{*.png, metadata.jsonl}   one folder per style
#   STYLES="rockart ukiyoe ..." (env) — which to train
# Produces /workspace/st/out/<style>/{lora/pytorch_lora_weights.safetensors, gate/*.png, gate/meta.json, sheet.jpg, train.log}
# plus out/base_gate/ (the shipped model with no LoRA, same captions, for the comparison line), SHA256SUMS, STYLES_DONE.
set -euo pipefail
cd /workspace/st
STEPS=${STEPS:-2000}; RANK=${RANK:-64}; SEEDS=${SEEDS:-2}
echo "### setup $(date -u +%FT%TZ)"
python -m pip install -q --break-system-packages "diffusers==0.31.0" "transformers==4.46.3" "accelerate==1.1.1" "peft==0.13.2" "datasets==3.1.0" safetensors pillow omegaconf 2>&1 | tail -1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
[ -d base/unet ] || python - <<'EOF'
import torch
from diffusers import StableDiffusionPipeline, UNet2DConditionModel
pipe = StableDiffusionPipeline.from_pretrained("common-canvas/CommonCanvas-S-C", torch_dtype=torch.float32, safety_checker=None)
pipe.unet = UNet2DConditionModel.from_single_file("/workspace/st/r1/pagouro-be-r3-fp16.safetensors", config="common-canvas/CommonCanvas-S-C", subfolder="unet", torch_dtype=torch.float32)
pipe.save_pretrained("/workspace/st/base"); print("base = shipped BE model, saved")
EOF
[ -f train_text_to_image_lora.py ] || curl -sL -o train_text_to_image_lora.py https://raw.githubusercontent.com/huggingface/diffusers/v0.31.0/examples/text_to_image/train_text_to_image_lora.py
mkdir -p out
cat > gate.py <<'EOF'
import json, os, sys, torch, time
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
style, lora_dir, out_dir, seeds = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
styles = json.load(open("/workspace/st/styles.json")); gate = [json.loads(l) for l in open("/workspace/st/gate40_styles.jsonl", encoding="utf-8")]
cfg = styles.get(style)
pipe = StableDiffusionPipeline.from_pretrained("/workspace/st/base", torch_dtype=torch.float16, safety_checker=None).to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config); pipe.set_progress_bar_config(disable=True)
if lora_dir != "none": pipe.load_lora_weights(lora_dir)
os.makedirs(out_dir, exist_ok=True); meta = []; t0 = time.time()
NEG = "photograph, photo, 3d render, blurry, watermark, text, lettering, words, caption, title, modern, gradient"
for g in gate:
    prompt = (f"{cfg['trigger']}, {cfg['phrase']}, {g['caption']}" if cfg else f"belleposter, Belle Epoque lithograph poster, {g['caption']}")
    for s in range(seeds):
        gen = torch.Generator("cuda").manual_seed(1000 + s)
        im = pipe(prompt, negative_prompt=NEG, num_inference_steps=30, guidance_scale=7.0, generator=gen).images[0]
        fn = f"{g['id']}_s{s}.png"; im.save(os.path.join(out_dir, fn))
        meta.append({"file": fn, "id": g["id"], "group": g["group"], "caption": g["caption"], "prompt": prompt, "seed": 1000 + s, "anatomy": g.get("anatomy", False)})
json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)
from PIL import Image
ids = sorted({m["id"] for m in meta}); W = 160
sheet = Image.new("RGB", (W * seeds, W * len(ids)), "white")
for r, i in enumerate(ids):
    for c in range(seeds): sheet.paste(Image.open(os.path.join(out_dir, f"{i}_s{c}.png")).resize((W, W)), (c * W, r * W))
sheet.save(os.path.join(os.path.dirname(out_dir), "sheet.jpg"), quality=80)
print(style, len(meta), "gate images", f"{time.time()-t0:.0f}s", flush=True)
EOF
[ -d out/base_gate/gate ] || { mkdir -p out/base_gate; python gate.py none none out/base_gate/gate $SEEDS; }
for st in $STYLES; do
  echo "### style $st: LoRA rank $RANK, $STEPS steps $(date -u +%FT%TZ)"; n=$(ls train/$st/512/*.png | wc -l); echo "training files: $n"
  mkdir -p out/$st
  accelerate launch --mixed_precision=bf16 train_text_to_image_lora.py \
    --pretrained_model_name_or_path=/workspace/st/base --train_data_dir=train/$st/512 --caption_column=text \
    --resolution=512 --random_flip --train_batch_size=8 --gradient_accumulation_steps=1 \
    --max_train_steps=$STEPS --learning_rate=1e-4 --lr_scheduler=cosine --lr_warmup_steps=50 \
    --rank=$RANK --seed=74 --checkpointing_steps=100000 --dataloader_num_workers=8 \
    --output_dir=/workspace/st/out/$st/lora 2>&1 | grep -vE "^\s*$" | tee out/$st/train.log | tail -3
  python gate.py $st out/$st/lora out/$st/gate $SEEDS
done
cd out && find . -type f ! -name SHA256SUMS -print0 | xargs -0 sha256sum > SHA256SUMS && du -sh . && cd ..
echo "STYLES_DONE $(date -u +%FT%TZ)"
