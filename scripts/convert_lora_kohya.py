"""Convert a diffusers/PEFT UNet LoRA (unet.<path>.lora_A.weight / lora_B.weight) to the kohya / webui naming
that stable-diffusion.cpp matches (lora_unet_<path with dots as underscores>.lora_down.weight / .lora_up.weight
plus an .alpha scalar). Pure header+tensor copy; no torch needed.

    python scripts/convert_lora_kohya.py <in.safetensors> <out.safetensors> [--alpha 64]
"""
from __future__ import annotations
import argparse, json, struct, sys


def read_safetensors(p):
    with open(p, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]; header = json.loads(f.read(n)); base = 8 + n
        data = f.read()
    tensors = {}
    for k, v in header.items():
        if k == "__metadata__": continue
        s, e = v["data_offsets"]; tensors[k] = (v["dtype"], v["shape"], data[s:e])
    return header.get("__metadata__") or {}, tensors


def write_safetensors(p, tensors, metadata):
    header = {"__metadata__": metadata}; blobs = []; off = 0
    for k in sorted(tensors):
        dtype, shape, raw = tensors[k]
        header[k] = {"dtype": dtype, "shape": shape, "data_offsets": [off, off + len(raw)]}; blobs.append(raw); off += len(raw)
    hb = json.dumps(header, separators=(",", ":")).encode()
    hb += b" " * ((8 - len(hb) % 8) % 8)
    with open(p, "wb") as f:
        f.write(struct.pack("<Q", len(hb))); f.write(hb)
        for b in blobs: f.write(b)


def to_ldm(p):
    """diffusers UNet attention path -> original Stable Diffusion (ldm) path, e.g.
    down_blocks.0.attentions.1.transformer_blocks.0.attn1.to_k -> input_blocks.2.1.transformer_blocks.0.attn1.to_k"""
    import re
    m = re.match(r"down_blocks\.(\d+)\.attentions\.(\d+)\.(.*)", p)
    if m: i, j, rest = int(m.group(1)), int(m.group(2)), m.group(3); return f"input_blocks.{3*i+j+1}.1.{rest}"
    m = re.match(r"up_blocks\.(\d+)\.attentions\.(\d+)\.(.*)", p)
    if m: i, j, rest = int(m.group(1)), int(m.group(2)), m.group(3); return f"output_blocks.{3*i+j}.1.{rest}"
    m = re.match(r"mid_block\.attentions\.0\.(.*)", p)
    if m: return f"middle_block.1.{m.group(1)}"
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--ldm", action="store_true", help="emit model.diffusion_model.<original SD path> names instead of kohya names")
    ap.add_argument("--no-alpha", action="store_true", help="write no .alpha scalars (the loader then scales by weight alone)")
    a = ap.parse_args()
    meta, t = read_safetensors(a.src)
    out = {}; ranks = set()
    for k, (dtype, shape, raw) in t.items():
        # diffusers writes either  <path>.lora_A.weight / .lora_B.weight  (PEFT)  or  <path>.lora.down.weight / .lora.up.weight
        if k.endswith(".lora_A.weight") or k.endswith(".lora.down.weight"):
            down = True; path = k[: -len(".lora_A.weight")] if k.endswith(".lora_A.weight") else k[: -len(".lora.down.weight")]
        elif k.endswith(".lora_B.weight") or k.endswith(".lora.up.weight"):
            down = False; path = k[: -len(".lora_B.weight")] if k.endswith(".lora_B.weight") else k[: -len(".lora.up.weight")]
        else:
            print("skip", k); continue
        if a.ldm and path.startswith("unet."):
            name = "model.diffusion_model." + to_ldm(path.split(".", 1)[1])
        else:
            prefix = "lora_unet_" if path.startswith("unet.") else "lora_te_" if path.startswith("text_encoder.") else "lora_"
            body = path.split(".", 1)[1] if "." in path else path
            name = prefix + body.replace(".", "_")
        out[name + (".lora_down.weight" if down else ".lora_up.weight")] = (dtype, shape, raw)
        if down: ranks.add(shape[0])
    rank = a.alpha if a.alpha is not None else (ranks.pop() if len(ranks) == 1 else max(ranks))
    # alpha = rank gives scale 1.0, which is how diffusers applied it in training/eval (lora_scale * alpha/rank)
    alpha_raw = struct.pack("<e", float(rank)) if list(t.values())[0][0] == "F16" else struct.pack("<f", float(rank))
    adtype = "F16" if list(t.values())[0][0] == "F16" else "F32"
    if not a.no_alpha:
        for n in [x[: -len(".lora_down.weight")] for x in out if x.endswith(".lora_down.weight")]:
            out[n + ".alpha"] = (adtype, [], alpha_raw)
    write_safetensors(a.dst, out, {**meta, "format": "pt", "converted": "pagouro convert_lora_kohya.py", "alpha": str(rank)})
    print(f"{a.src} -> {a.dst}: {len(out)} tensors, rank/alpha {rank}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
