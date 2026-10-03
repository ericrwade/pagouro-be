"""Upload the Pagouro BE Styles pack to Hugging Face as its own public model repo (BE 1.0's repo stays as shipped).
Token: HF_TOKEN from PAGOURO_BUILD/.env (never printed). Uploads the pack folder as-is plus the release zip and its
sha256, then verifies the zip's SHA-256 against the store.

    python scripts/hf_upload_styles.py [--repo Pagouro/pagouro-be-styles-1.0]
"""
from __future__ import annotations
import argparse, hashlib, io, os, sys

BE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.abspath(os.path.join(BE, "..", "PAGOURO_BUILD"))
PACK = os.path.join(BE, "release", "Pagouro-BE-Styles-1.0")
ZIP = os.path.join(BE, "release", "dist", "Pagouro-BE-Styles-1.0.zip")


def token():
    for line in io.open(os.path.join(BUILD, ".env"), encoding="utf-8"):
        if line.startswith("HF_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("HF_TOKEN not in .env")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Pagouro/pagouro-be-styles-1.0")
    a = ap.parse_args()
    from huggingface_hub import HfApi
    api = HfApi(token=token())
    api.create_repo(a.repo, repo_type="model", private=False, exist_ok=True)
    print("repo", a.repo, "ready", flush=True)
    api.upload_folder(folder_path=PACK, path_in_repo=".", repo_id=a.repo, repo_type="model",
                      commit_message="Pagouro BE Styles 1.0 pack (signed manifest inside)")
    print("pack folder uploaded", flush=True)
    for src, dst in ((ZIP, "Pagouro-BE-Styles-1.0.zip"), (ZIP + ".sha256", "Pagouro-BE-Styles-1.0.zip.sha256")):
        api.upload_file(path_or_fileobj=src, path_in_repo=dst, repo_id=a.repo, repo_type="model")
        print("uploaded", dst, flush=True)
    info = api.model_info(a.repo, files_metadata=True)
    remote = {s.rfilename: s for s in info.siblings}
    z = remote.get("Pagouro-BE-Styles-1.0.zip")
    local = sha256(ZIP)
    print("zip remote sha256", (z.lfs.sha256 if z and z.lfs else "?")[:16], "local", local[:16],
          "MATCH" if z and z.lfs and z.lfs.sha256 == local else "CHECK")
    print("files on HF:", len(remote))
    return 0


if __name__ == "__main__":
    sys.exit(main())
