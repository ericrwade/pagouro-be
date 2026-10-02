# Decode the styles gate for given styles at reduced LoRA weights, to find the weight the pack recommends.
#   python gate_scale.py "rockart greekvase naturalhistory" "0.6 0.8" 2
import json, os, sys, time, torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
styles_arg, scales_arg, seeds = sys.argv[1].split(), [float(x) for x in sys.argv[2].split()], int(sys.argv[3])
styles = json.load(open("/workspace/st/styles.json")); gate = [json.loads(l) for l in open("/workspace/st/gate40_styles.jsonl", encoding="utf-8")]
NEG = "photograph, photo, 3d render, blurry, watermark, text, lettering, words, caption, title, modern, gradient"
for st in styles_arg:
    cfg = styles[st]
    for sc in scales_arg:
        pipe = StableDiffusionPipeline.from_pretrained("/workspace/st/base", torch_dtype=torch.float16, safety_checker=None).to("cuda")
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config); pipe.set_progress_bar_config(disable=True)
        pipe.load_lora_weights(f"/workspace/st/out/{st}/lora"); pipe.fuse_lora(lora_scale=sc)
        tag = f"gate_w{int(sc*100):02d}"; out_dir = f"/workspace/st/out/{st}/{tag}"; os.makedirs(out_dir, exist_ok=True)
        meta = []; t0 = time.time()
        for g in gate:
            prompt = f"{cfg['trigger']}, {cfg['phrase']}, {g['caption']}"
            for s in range(seeds):
                gen = torch.Generator("cuda").manual_seed(1000 + s)
                im = pipe(prompt, negative_prompt=NEG, num_inference_steps=30, guidance_scale=7.0, generator=gen).images[0]
                fn = f"{g['id']}_s{s}.png"; im.save(os.path.join(out_dir, fn))
                meta.append({"file": fn, "id": g["id"], "group": g["group"], "caption": g["caption"], "prompt": prompt, "seed": 1000 + s, "anatomy": g.get("anatomy", False), "lora_scale": sc})
        json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)
        ids = sorted({m["id"] for m in meta}); W = 160
        sheet = Image.new("RGB", (W * seeds, W * len(ids)), "white")
        for r, i in enumerate(ids):
            for c in range(seeds): sheet.paste(Image.open(os.path.join(out_dir, f"{i}_s{c}.png")).resize((W, W)), (c * W, r * W))
        sheet.save(f"/workspace/st/out/{st}/sheet_{tag}.jpg", quality=80)
        print(st, tag, len(meta), "images", f"{time.time()-t0:.0f}s", flush=True)
        del pipe; torch.cuda.empty_cache()
print("GATE_SCALE_DONE")
