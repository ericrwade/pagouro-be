#!/usr/bin/env bash
# O-37 route B: a Belle Époque style LoRA on CommonCanvas-S-C (CC-BY-SA-4.0 weights, trained on
# CC-BY/CC-BY-SA images), fine-tuned on our own poster slice, then a candidate pass of hermit-crab
# marks. Runs on a RunPod A40. Everything it produces lands in /workspace/belle/out and is fetched
# home before the pod is deleted.
#
#   bash belle_lora.sh            (expects /workspace/belle/train/512/{*.png,metadata.jsonl} uploaded)
set -euo pipefail
cd /workspace/belle
echo "### setup"
python -m pip install -q --break-system-packages "diffusers==0.31.0" "transformers==4.46.3" "accelerate==1.1.1" "peft==0.13.2" "datasets==3.1.0" safetensors pillow omegaconf 2>&1 | tail -1
python - <<'EOF'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0))
EOF
echo "### base model -> diffusers format"
[ -d /workspace/belle/base/unet ] || python - <<'EOF'
from diffusers import StableDiffusionPipeline
import torch
pipe = StableDiffusionPipeline.from_pretrained("common-canvas/CommonCanvas-S-C", safety_checker=None)   # fp32 on disk: LoRA params must be fp32 under fp16 mixed precision
pipe.save_pretrained("/workspace/belle/base")
print("base saved; unet params", sum(p.numel() for p in pipe.unet.parameters()) / 1e6, "M")
EOF
echo "### LoRA training (diffusers text-to-image LoRA script)"
[ -f train_text_to_image_lora.py ] || curl -sL -o train_text_to_image_lora.py https://raw.githubusercontent.com/huggingface/diffusers/v0.31.0/examples/text_to_image/train_text_to_image_lora.py
accelerate launch --mixed_precision=bf16 train_text_to_image_lora.py \
  --pretrained_model_name_or_path=/workspace/belle/base \
  --train_data_dir=/workspace/belle/train/512 --caption_column=text \
  --resolution=512 --random_flip --train_batch_size=8 --gradient_accumulation_steps=1 \
  --max_train_steps=${STEPS:-1500} --learning_rate=1e-4 --lr_scheduler=cosine --lr_warmup_steps=50 \
  --rank=32 --seed=74 --checkpointing_steps=500 --dataloader_num_workers=4 \
  --output_dir=/workspace/belle/out/lora 2>&1 | grep -vE "^\s*$" | tail -30
echo "### candidates"
python - <<'EOF'
import os, torch, json
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("/workspace/belle/base", torch_dtype=torch.float16, safety_checker=None).to("cuda")
pipe.load_lora_weights("/workspace/belle/out/lora")
os.makedirs("/workspace/belle/out/crabs", exist_ok=True)
prompts = [
 "belleposter, Belle Époque lithograph poster, a hermit crab retreated into its spiral shell, only the claws and eyes showing, flat colour planes, bold black contour, cream paper, vermilion and chrome yellow, circular medallion",
 "belleposter, Belle Époque lithograph poster, emblem of a hermit crab in a spiral shell, claws and eyes at the mouth of the shell, Prussian blue and gold, ornamental border, hand lettering",
 "belleposter, Belle Époque lithograph poster by Jules Chéret, a hermit crab shell with eyes peeking out, sunburst behind, flat colours, one heavy contour",
 "belleposter, Belle Époque lithograph poster in the manner of Mucha, a hermit crab curled in a spiral shell inside a round cartouche, sage and dusty rose, gold outlines",
 "belleposter, Belle Époque lithograph poster by Steinlen, a hermit crab in its shell seen from the front, claws folded, cast shadow, cream and vermilion",
 "belleposter, Belle Époque poster logo, a hermit crab shell with two eyes and folded claws, bold silhouette, two colours on cream, medallion",
]
g = torch.Generator("cuda")
meta = []
n = 0
for pi, p in enumerate(prompts):
    for s in range(int(os.environ.get("PER_PROMPT", "20"))):
        seed = 1000 * pi + s
        g.manual_seed(seed)
        im = pipe(p, negative_prompt="photograph, photo, realistic, 3d render, blurry, text watermark, modern, gradient", num_inference_steps=30, guidance_scale=7.0, generator=g, height=512, width=512).images[0]
        fn = f"/workspace/belle/out/crabs/crab_{pi}_{s:02d}.png"
        im.save(fn); meta.append({"file": os.path.basename(fn), "prompt": p, "seed": seed}); n += 1
json.dump(meta, open("/workspace/belle/out/crabs/meta.json", "w"), indent=1)
print("candidates:", n)
EOF
echo "BELLE_DONE"
