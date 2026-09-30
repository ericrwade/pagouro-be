r"""GitHub caps a release asset at 2 GiB and the model alone is 2.58 GB, so the release page carries the stick in
two pieces (everything is still one zip on Hugging Face / Arweave, hash f6a059dd…):

  Pagouro-BE-1.0-win64-kit.zip        the stick without model/ (runtime, docs, ledgers, evals, manifest, signature)
  pagouro-be-1.0-f16.gguf.part1/.part2 the model file, split at 2,000,000,000 bytes
  JOIN-MODEL.bat                       run inside the unzipped Pagouro-BE folder with the two parts beside it:
                                       joins them into model\pagouro-be-1.0-f16.gguf and checks the SHA-256
Also writes .sha256 files for the kit and the model.

    python scripts/split_release.py --version 1.0
"""
from __future__ import annotations
import argparse, hashlib, io, os, sys, zipfile

BE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PART = 2_000_000_000


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="1.0")
    a = ap.parse_args()
    src = os.path.join(BE, "release", f"Pagouro-BE-{a.version}")
    dist = os.path.join(BE, "release", "dist")
    model = os.path.join(src, "model", f"pagouro-be-{a.version}-f16.gguf")
    msha = sha256(model)
    # kit zip
    kit = os.path.join(dist, f"Pagouro-BE-{a.version}-win64-kit.zip")
    n = 0
    with zipfile.ZipFile(kit, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dirpath, dirs, files in os.walk(src):
            dirs.sort()
            if os.path.basename(dirpath) == "model":
                continue
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                z.write(p, "Pagouro-BE/" + os.path.relpath(p, src).replace(os.sep, "/"))
                n += 1
        z.writestr("Pagouro-BE/model/README.txt",
                   f"Put pagouro-be-{a.version}-f16.gguf here (SHA-256 {msha}).\n"
                   "Either run JOIN-MODEL.bat from the release page with the two .part files beside this folder,\n"
                   "or download the file from https://huggingface.co/Pagouro/pagouro-be-1.0 and copy it here.\n"
                   "Then VERIFY.bat must say every listed file matches the manifest.\n")
    open(kit + ".sha256", "w").write(sha256(kit) + "\n")
    # model parts
    parts = []
    with open(model, "rb") as f:
        i = 1
        while True:
            chunk = f.read(PART)
            if not chunk:
                break
            p = os.path.join(dist, f"pagouro-be-{a.version}-f16.gguf.part{i}")
            open(p, "wb").write(chunk)
            parts.append(p)
            i += 1
    open(os.path.join(dist, f"pagouro-be-{a.version}-f16.gguf.sha256"), "w").write(msha + "\n")
    bat = "\r\n".join([
        "@echo off",
        "REM Joins the two model parts from the release page into model\\pagouro-be-%V%-f16.gguf and checks its SHA-256.",
        "REM Run this inside the unzipped Pagouro-BE folder, with the .part1 and .part2 files in the same folder.",
        f"set V={a.version}",
        f"set EXPECT={msha}",
        "setlocal",
        "cd /d \"%~dp0\"",
        "if not exist pagouro-be-%V%-f16.gguf.part1 echo Missing pagouro-be-%V%-f16.gguf.part1 next to this file. && exit /b 1",
        "if not exist pagouro-be-%V%-f16.gguf.part2 echo Missing pagouro-be-%V%-f16.gguf.part2 next to this file. && exit /b 1",
        "if not exist model mkdir model",
        "echo Joining (2.6 GB, a minute or two) ...",
        "copy /b pagouro-be-%V%-f16.gguf.part1+pagouro-be-%V%-f16.gguf.part2 model\\pagouro-be-%V%-f16.gguf >nul",
        "echo Checking SHA-256 ...",
        "for /f \"skip=1 tokens=* delims=\" %%h in ('certutil -hashfile model\\pagouro-be-%V%-f16.gguf SHA256 ^| findstr /v /i \"certutil\"') do (set GOT=%%h & goto :done)",
        ":done",
        "set GOT=%GOT: =%",
        "if /i \"%GOT%\"==\"%EXPECT%\" (echo OK: model\\pagouro-be-%V%-f16.gguf matches %EXPECT% && del pagouro-be-%V%-f16.gguf.part1 pagouro-be-%V%-f16.gguf.part2) else (echo MISMATCH: got %GOT% expected %EXPECT% -- do not use this file)",
        "endlocal",
        ""])
    io.open(os.path.join(dist, "JOIN-MODEL.bat"), "w", encoding="ascii", newline="").write(bat)
    print(f"kit {n} files {os.path.getsize(kit):,} B; parts {[os.path.getsize(p) for p in parts]}; model sha {msha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
