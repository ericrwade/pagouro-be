"""Pagouro BE showcase x180 — pod side generation.

Draws every caption in /workspace/sc/captions.jsonl with the shipped BE 1.0 model, N seeds each, with the
exact settings the gate was measured with (gate.py in styles_train.sh): diffusers StableDiffusionPipeline
built from the CommonCanvas-S-C config + the single-file BE UNet, fp16, DPM++ 2M (DPMSolverMultistep),
30 steps, guidance 7, 512x512, negative prompt as trained.

    python showcase_gen.py /workspace/sc/captions.jsonl /workspace/sc/raw "1000 1001 1002"
"""
import json, os, sys, time, torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, UNet2DConditionModel
from huggingface_hub import hf_hub_download

caps_path, out_dir, seeds = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3].split()]
BASE = "/workspace/sc/base"
if not os.path.isdir(os.path.join(BASE, "unet")):
    f = hf_hub_download("Pagouro/pagouro-be-1.0", "pagouro-be-1.0-fp16.safetensors")
    print("model file", f, os.path.getsize(f), flush=True)
    pipe = StableDiffusionPipeline.from_pretrained("common-canvas/CommonCanvas-S-C", torch_dtype=torch.float32, safety_checker=None)
    pipe.unet = UNet2DConditionModel.from_single_file(f, config="common-canvas/CommonCanvas-S-C", subfolder="unet", torch_dtype=torch.float32)
    pipe.save_pretrained(BASE)
    print("base = shipped BE 1.0 model, saved", flush=True)
    del pipe
pipe = StableDiffusionPipeline.from_pretrained(BASE, torch_dtype=torch.float16, safety_checker=None).to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.set_progress_bar_config(disable=True)
rows = [json.loads(l) for l in open(caps_path, encoding="utf-8")]
os.makedirs(out_dir, exist_ok=True)
meta_path = os.path.join(out_dir, "meta.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else []
done = {m["file"] for m in meta}
t0 = time.time()
for r in rows:
    for s in seeds:
        fn = f"{r['number']:03d}-{r['slug']}_s{s}.png"
        if fn in done:
            continue
        gen = torch.Generator("cuda").manual_seed(s)
        im = pipe(r["prompt"], negative_prompt=r["negative"], num_inference_steps=30, guidance_scale=7.0,
                  width=512, height=512, generator=gen).images[0]
        im.save(os.path.join(out_dir, fn))
        meta.append({"file": fn, "number": r["number"], "slug": r["slug"], "category": r["category"],
                     "caption": r["caption"], "prompt": r["prompt"], "negative": r["negative"], "seed": s,
                     "steps": 30, "guidance": 7.0, "sampler": "DPM++ 2M (diffusers DPMSolverMultistepScheduler)",
                     "size": 512})
    if r["number"] % 20 == 0:
        json.dump(meta, open(meta_path, "w"), indent=1)
        print(f"{r['number']}/{len(rows)} prompts, {len(meta)} pictures, {time.time()-t0:.0f}s", flush=True)
json.dump(meta, open(meta_path, "w"), indent=1)
print("GEN_DONE", len(meta), "pictures", f"{time.time()-t0:.0f}s", flush=True)
