"""Upload Pagouro BE 1.0 to Hugging Face (private until the flip). Token: HF_TOKEN from PAGOURO_BUILD/.env
(never printed). Verifies each large file's SHA-256 against the store after upload.

    python scripts/hf_upload.py [--repo Pagouro/pagouro-be-1.0] [--public]
"""
from __future__ import annotations
import argparse, hashlib, io, os, sys

BE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.abspath(os.path.join(BE, "..", "PAGOURO_BUILD"))
STICK = os.path.join(BE, "release", "Pagouro-BE-1.0")


def token():
    for line in io.open(os.path.join(BUILD, ".env"), encoding="utf-8"):
        if line.startswith("HF_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no HF_TOKEN")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Pagouro/pagouro-be-1.0")
    ap.add_argument("--public", action="store_true")
    a = ap.parse_args()
    from huggingface_hub import HfApi
    api = HfApi(token=token())
    api.create_repo(a.repo, repo_type="model", private=not a.public, exist_ok=True)
    files = [
        (os.path.join(STICK, "model", "pagouro-be-1.0-f16.gguf"), "pagouro-be-1.0-f16.gguf"),
        (os.path.join(BE, "runs", "round3", "ft_single", "pagouro-be-r3-fp16.safetensors"), "pagouro-be-1.0-fp16.safetensors"),
        (os.path.join(STICK, "MANIFEST.md"), "MANIFEST.md"),
        (os.path.join(STICK, "MANIFEST.md.minisig"), "MANIFEST.md.minisig"),
        (os.path.join(STICK, "pagouro.pub"), "pagouro.pub"),
        (os.path.join(STICK, "CORPUS.md"), "CORPUS.md"),
        (os.path.join(STICK, "facts.json"), "facts.json"),
        (os.path.join(STICK, "LICENSES.md"), "LICENSES.md"),
        (os.path.join(STICK, "CHECK_YOUR_COPY.md"), "CHECK_YOUR_COPY.md"),
        (os.path.join(BE, "docs", "MODEL_CARD.md"), "README.md"),
    ]
    ots = os.path.join(BE, "docs", "MANIFEST_v1.0.md.ots")
    if os.path.exists(ots):
        files.append((ots, "MANIFEST.md.ots"))
    for src, dst in files:
        print("upload", dst, f"{os.path.getsize(src):,} B", flush=True)
        api.upload_file(path_or_fileobj=src, path_in_repo=dst, repo_id=a.repo, repo_type="model")
    for folder, dst in ((os.path.join(STICK, "ledger"), "ledger"), (os.path.join(STICK, "evals"), "evals")):
        print("upload folder", dst, flush=True)
        api.upload_folder(folder_path=folder, path_in_repo=dst, repo_id=a.repo, repo_type="model")
    # verify the large files' LFS hashes
    info = api.model_info(a.repo, files_metadata=True)
    lfs = {s.rfilename: (s.lfs.sha256 if s.lfs else None) for s in info.siblings}
    for src, dst in files[:2]:
        local = sha256(src)
        print(dst, "local", local[:16], "hub", (lfs.get(dst) or "?")[:16], "MATCH" if lfs.get(dst) == local else "MISMATCH")
    print("done:", f"https://huggingface.co/{a.repo}", "private" if not a.public else "public")
    return 0


if __name__ == "__main__":
    sys.exit(main())
