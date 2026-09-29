#!/usr/bin/env bash
# Pagouro BE round 2 (D-99) on one A100 80 GB. Expects, uploaded to /workspace/be:
#   train/512/{*.png,metadata.jsonl}   the round-2 set (lettering suffix in captions)
#   gate40.jsonl
#   r1/pagouro-be-r1-fp16.safetensors  the round-1 fine-tune as a single SD2 file (start point)
# Produces under /workspace/be/out:
#   ft/           round-2 UNet (diffusers layout)
#   ft_single/    pagouro-be-r2-fp16.safetensors
#   gate/{ft, ft_neg}/  40 captions x 4 seeds: plain decode, and with the lettering negative prompt
#                        on captions that ask for no words
#   SHA256SUMS, train_ft.log
# Ends by printing BE_ROUND2_DONE.
set -euo pipefail
cd /workspace/be
STEPS_FT=${STEPS_FT:-8000}
SEEDS=${SEEDS:-4}
echo "### setup $(date -u +%FT%TZ)"
python -m pip install -q --break-system-packages "diffusers==0.31.0" "transformers==4.46.3" "accelerate==1.1.1" "peft==0.13.2" "datasets==3.1.0" safetensors pillow omegaconf 2>&1 | tail -1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "### start point: round-1 single file -> diffusers layout (fp32 for training)"
[ -d base/unet ] || python - <<'EOF'
from diffusers import StableDiffusionPipeline
import torch
# the SD2 config repos on the Hub are gated (401) and the single file's text encoder does not map back through
# diffusers' loader; only the UNet changed in round 1, so: base pipeline from CommonCanvas (config, text encoder,
# VAE) + the round-1 UNet weights read out of the single file.
from diffusers import UNet2DConditionModel
pipe = StableDiffusionPipeline.from_pretrained("common-canvas/CommonCanvas-S-C", torch_dtype=torch.float32, safety_checker=None)
pipe.unet = UNet2DConditionModel.from_single_file("/workspace/be/r1/pagouro-be-r1-fp16.safetensors", config="common-canvas/CommonCanvas-S-C", subfolder="unet", torch_dtype=torch.float32)
pipe.save_pretrained("/workspace/be/base")
print("start point saved; prediction", pipe.scheduler.config.get("prediction_type"))
EOF
[ -f train_text_to_image.py ] || curl -sL -o train_text_to_image.py https://raw.githubusercontent.com/huggingface/diffusers/v0.31.0/examples/text_to_image/train_text_to_image.py
n=$(ls train/512/*.png | wc -l); echo "training images: $n"; grep -c "no lettering" train/512/metadata.jsonl || true
mkdir -p out
echo "### full UNet fine-tune from round 1, $STEPS_FT steps $(date -u +%FT%TZ)"
accelerate launch --mixed_precision=bf16 train_text_to_image.py \
  --pretrained_model_name_or_path=/workspace/be/base \
  --train_data_dir=train/512 --caption_column=text --image_column=image \
  --resolution=512 --random_flip --train_batch_size=16 --gradient_accumulation_steps=1 --gradient_checkpointing \
  --max_train_steps=$STEPS_FT --learning_rate=8e-6 --lr_scheduler=cosine --lr_warmup_steps=200 \
  --use_ema --snr_gamma=5.0 --noise_offset=0.05 --seed=75 --checkpointing_steps=2000 --checkpoints_total_limit=1 \
  --dataloader_num_workers=8 --output_dir=/workspace/be/out/ft 2>&1 | grep -vE "^\s*$" | tee out/train_ft.log | tail -5
echo "### gate: ft plain + ft with lettering negative $(date -u +%FT%TZ)"
SEEDS=$SEEDS python - <<'EOF'
import json, os, torch, time
from diffusers import StableDiffusionPipeline, UNet2DConditionModel, DPMSolverMultistepScheduler
gate = [json.loads(l) for l in open("/workspace/be/gate40.jsonl", encoding="utf-8")]
SEEDS = int(os.environ["SEEDS"])
NEG = "photograph, photo, realistic, 3d render, blurry, watermark, modern, gradient"
NEG_LET = NEG + ", text, lettering, letters, words, writing, caption, title"
pipe = StableDiffusionPipeline.from_pretrained("/workspace/be/base", torch_dtype=torch.float16, safety_checker=None)
pipe.unet = UNet2DConditionModel.from_pretrained("/workspace/be/out/ft", subfolder="unet", torch_dtype=torch.float16)
pipe = pipe.to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.set_progress_bar_config(disable=True)
for name, use_neg in (("ft", False), ("ft_neg", True)):
    d = f"/workspace/be/out/gate/{name}"; os.makedirs(d, exist_ok=True)
    meta = []; t0 = time.time()
    for g in gate:
        prompt = f"belleposter, Belle Époque lithograph poster, {g['caption']}"
        neg = NEG_LET if (use_neg and not g["expect_text"]) else NEG
        if use_neg and not g["expect_text"]:
            prompt += ", no lettering"
        for s in range(SEEDS):
            gen = torch.Generator("cuda").manual_seed(1000 + s)
            im = pipe(prompt, negative_prompt=neg, num_inference_steps=30, guidance_scale=7.0, generator=gen).images[0]
            fn = f"{g['id']}_s{s}.png"; im.save(os.path.join(d, fn))
            meta.append({"file": fn, "id": g["id"], "group": g["group"], "caption": g["caption"], "prompt": prompt, "negative": neg, "seed": 1000 + s})
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    print(name, len(meta), "images", f"{time.time()-t0:.0f}s", flush=True)
EOF
echo "### single-file SD2 checkpoint (fp16) $(date -u +%FT%TZ)"
[ -f convert_diffusers_to_original_stable_diffusion.py ] || curl -sL -o convert_diffusers_to_original_stable_diffusion.py https://raw.githubusercontent.com/huggingface/diffusers/v0.31.0/scripts/convert_diffusers_to_original_stable_diffusion.py
python - <<'EOF'
from diffusers import StableDiffusionPipeline, UNet2DConditionModel
p = StableDiffusionPipeline.from_pretrained("/workspace/be/base", safety_checker=None)
p.unet = UNet2DConditionModel.from_pretrained("/workspace/be/out/ft", subfolder="unet")
p.save_pretrained("/workspace/be/out/ft_pipe"); print("ft_pipe saved")
EOF
mkdir -p out/ft_single
python convert_diffusers_to_original_stable_diffusion.py --model_path /workspace/be/out/ft_pipe --checkpoint_path /workspace/be/out/ft_single/pagouro-be-r2-fp16.safetensors --half --use_safetensors
ls -l out/ft_single
python - <<'EOF'
from PIL import Image
import json
for arm in ("ft", "ft_neg"):
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
echo "BE_ROUND2_DONE $(date -u +%FT%TZ)"
