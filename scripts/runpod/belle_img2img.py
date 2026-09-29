import os, json, torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline
pipe = StableDiffusionImg2ImgPipeline.from_pretrained("/workspace/belle/base", torch_dtype=torch.float16, safety_checker=None).to("cuda")
pipe.load_lora_weights("/workspace/belle/out/lora")
os.makedirs("/workspace/belle/out/crabs2", exist_ok=True)
P = ["belleposter, Belle Époque lithograph poster, a hermit crab retreated into its spiral shell, only two folded claws and two eyes on stalks showing at the mouth of the shell, flat colour planes, one heavy black contour, cream paper, sunburst medallion",
     "belleposter, Belle Époque lithograph poster by Jules Chéret, emblem: a snail-like spiral shell with a hermit crab's eyes and claws peeking out, vermilion, chrome yellow, Prussian blue, cast shadow, round cartouche",
     "belleposter, Belle Époque poster logo in the manner of Steinlen, a hermit crab hiding in its shell, claws folded under the lip, eyes peeking, bold silhouette, two colours on cream, medallion"]
g = torch.Generator("cuda"); meta = []; n = 0
for k in range(6):
    init = Image.open(f"/workspace/belle/init/mark_{k}.png").convert("RGB").resize((512, 512))
    for pi, p in enumerate(P):
        for strength in (0.55, 0.7):
            for s in range(2):
                seed = 5000 + k * 100 + pi * 10 + int(strength * 10) + s
                g.manual_seed(seed)
                im = pipe(prompt=p, image=init, strength=strength, guidance_scale=7.5, num_inference_steps=40, generator=g,
                          negative_prompt="photograph, realistic, 3d render, blurry, modern, gradient, lobster, spider, face").images[0]
                fn = f"/workspace/belle/out/crabs2/i2i_{k}_{pi}_{int(strength*100)}_{s}.png"
                im.save(fn); meta.append({"file": os.path.basename(fn), "init": f"mark_{k}", "prompt": p, "strength": strength, "seed": seed}); n += 1
json.dump(meta, open("/workspace/belle/out/crabs2/meta.json", "w"), indent=1)
print("img2img candidates:", n)
