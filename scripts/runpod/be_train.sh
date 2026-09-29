#!/usr/bin/env bash
# Pagouro BE round 1 (D-98) on one A100 80 GB. Expects /workspace/be/train/512/{*.png,metadata.jsonl}
# and /workspace/be/gate40.jsonl uploaded. Produces, under /workspace/be/out:
#   ft/           full UNet fine-tune of CommonCanvas-S-C (diffusers layout, fp16 unet)
#   ft_single/    the same as one SD2-layout safetensors file (for stable-diffusion.cpp)
#   lora/         the LoRA control arm
#   gate/{base,ft,lora}/  40 captions x 4 seeds each, plus meta.json
#   SHA256SUMS, train_ft.log, train_lora.log
# Ends by printing BE_ROUND1_DONE. Everything is fetched home before the pod is deleted.
set -euo pipefail
cd /workspace/be
STEPS_FT=${STEPS_FT:-5000}
STEPS_LORA=${STEPS_LORA:-2000}
SEEDS=${SEEDS:-4}
echo "### setup $(date -u +%FT%TZ)"
python -m pip install -q --break-system-packages "diffusers==0.31.0" "transformers==4.46.3" "accelerate==1.1.1" "peft==0.13.2" "datasets==3.1.0" safetensors pillow omegaconf bitsandbytes 2>&1 | tail -1
python - <<'EOF'
import torch; print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0))
EOF
nvidia-smi --query-gpu=memory.total --format=csv,noheader
echo "### base model (CommonCanvas-S-C, CC-BY-SA-4.0) -> diffusers fp32 on disk"
[ -d base/unet ] || python - <<'EOF'
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("common-canvas/CommonCanvas-S-C", safety_checker=None)
pipe.save_pretrained("/workspace/be/base")
print("unet params M", sum(p.numel() for p in pipe.unet.parameters())/1e6, "text enc M", sum(p.numel() for p in pipe.text_encoder.parameters())/1e6)
print("scheduler", pipe.scheduler.config.get("prediction_type"))
EOF
for s in train_text_to_image.py train_text_to_image_lora.py; do
  [ -f $s ] || curl -sL -o $s https://raw.githubusercontent.com/huggingface/diffusers/v0.31.0/examples/text_to_image/$s
done
n=$(ls train/512/*.png | wc -l); echo "training images: $n"
mkdir -p out
echo "### arm A: full UNet fine-tune, $STEPS_FT steps $(date -u +%FT%TZ)"
accelerate launch --mixed_precision=bf16 train_text_to_image.py \
  --pretrained_model_name_or_path=/workspace/be/base \
  --train_data_dir=train/512 --caption_column=text --image_column=image \
  --resolution=512 --random_flip --train_batch_size=16 --gradient_accumulation_steps=1 --gradient_checkpointing \
  --max_train_steps=$STEPS_FT --learning_rate=1e-5 --lr_scheduler=cosine --lr_warmup_steps=200 \
  --use_ema --snr_gamma=5.0 --noise_offset=0.05 --seed=74 --checkpointing_steps=1000 --checkpoints_total_limit=2 \
  --dataloader_num_workers=8 --output_dir=/workspace/be/out/ft 2>&1 | grep -vE "^\s*$" | tee out/train_ft.log | tail -5
echo "### arm B: LoRA rank 64, $STEPS_LORA steps $(date -u +%FT%TZ)"
accelerate launch --mixed_precision=bf16 train_text_to_image_lora.py \
  --pretrained_model_name_or_path=/workspace/be/base \
  --train_data_dir=train/512 --caption_column=text \
  --resolution=512 --random_flip --train_batch_size=8 --gradient_accumulation_steps=1 \
  --max_train_steps=$STEPS_LORA --learning_rate=1e-4 --lr_scheduler=cosine --lr_warmup_steps=50 \
  --rank=64 --seed=74 --checkpointing_steps=1000 --dataloader_num_workers=8 \
  --output_dir=/workspace/be/out/lora 2>&1 | grep -vE "^\s*$" | tee out/train_lora.log | tail -5
echo "### gate: 40 captions x $SEEDS seeds x {base, ft, lora} $(date -u +%FT%TZ)"
SEEDS=$SEEDS python - <<'EOF'
import json, os, torch, time
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
gate = [json.loads(l) for l in open("/workspace/be/gate40.jsonl", encoding="utf-8")]
SEEDS = int(os.environ["SEEDS"])
NEG = "photograph, photo, realistic, 3d render, blurry, watermark, modern, gradient"
def run(name, load):
    pipe = load()
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.set_progress_bar_config(disable=True)
    d = f"/workspace/be/out/gate/{name}"; os.makedirs(d, exist_ok=True)
    meta = []; t0 = time.time()
    for g in gate:
        prompt = f"belleposter, Belle Époque lithograph poster, {g['caption']}"
        for s in range(SEEDS):
            gen = torch.Generator("cuda").manual_seed(1000 + s)
            im = pipe(prompt, negative_prompt=NEG, num_inference_steps=30, guidance_scale=7.0, generator=gen).images[0]
            fn = f"{g['id']}_s{s}.png"; im.save(os.path.join(d, fn))
            meta.append({"file": fn, "id": g["id"], "group": g["group"], "caption": g["caption"], "prompt": prompt, "seed": 1000 + s})
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    print(name, len(meta), "images", f"{time.time()-t0:.0f}s", flush=True)
    del pipe; torch.cuda.empty_cache()
base = lambda: StableDiffusionPipeline.from_pretrained("/workspace/be/base", torch_dtype=torch.float16, safety_checker=None).to("cuda")
run("base", base)
def ft():
    p = StableDiffusionPipeline.from_pretrained("/workspace/be/base", torch_dtype=torch.float16, safety_checker=None)
    from diffusers import UNet2DConditionModel
    p.unet = UNet2DConditionModel.from_pretrained("/workspace/be/out/ft", subfolder="unet", torch_dtype=torch.float16)
    return p.to("cuda")
run("ft", ft)
def lora():
    p = base(); p.load_lora_weights("/workspace/be/out/lora"); return p
run("lora", lora)
EOF
echo "### single-file SD2 checkpoint of arm A (fp16) for stable-diffusion.cpp $(date -u +%FT%TZ)"
[ -f convert_diffusers_to_original_stable_diffusion.py ] || curl -sL -o convert_diffusers_to_original_stable_diffusion.py https://raw.githubusercontent.com/huggingface/diffusers/v0.31.0/scripts/convert_diffusers_to_original_stable_diffusion.py
python - <<'EOF'
# assemble a full pipeline folder with the fine-tuned unet, then convert
from diffusers import StableDiffusionPipeline, UNet2DConditionModel
import torch
p = StableDiffusionPipeline.from_pretrained("/workspace/be/base", safety_checker=None)
p.unet = UNet2DConditionModel.from_pretrained("/workspace/be/out/ft", subfolder="unet")
p.save_pretrained("/workspace/be/out/ft_pipe")
print("ft_pipe saved")
EOF
mkdir -p out/ft_single
python convert_diffusers_to_original_stable_diffusion.py --model_path /workspace/be/out/ft_pipe --checkpoint_path /workspace/be/out/ft_single/pagouro-be-r1-fp16.safetensors --half --use_safetensors
ls -l out/ft_single
echo "### contact sheets + hashes"
python - <<'EOF'
from PIL import Image
import json, os
for arm in ("base", "ft", "lora"):
    d = f"/workspace/be/out/gate/{arm}"; meta = json.load(open(f"{d}/meta.json"))
    ids = sorted({m["id"] for m in meta}); seeds = sorted({m["seed"] for m in meta})
    W = 160; sheet = Image.new("RGB", (W * len(seeds), W * len(ids)), "white")
    for r, i in enumerate(ids):
        for c, s in enumerate(seeds):
            sheet.paste(Image.open(f"{d}/{i}_s{s-1000}.png").resize((W, W)), (c * W, r * W))
    sheet.save(f"/workspace/be/out/gate/sheet_{arm}.jpg", quality=80)
print("sheets ok")
EOF
rm -rf out/ft_pipe out/ft/checkpoint-*
cd out && find . -type f ! -name SHA256SUMS -print0 | xargs -0 sha256sum > SHA256SUMS && du -sh . && cd ..
echo "BE_ROUND1_DONE $(date -u +%FT%TZ)"
