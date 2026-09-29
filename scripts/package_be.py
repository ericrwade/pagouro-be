"""Package Pagouro BE for a USB stick / zip (D-98 packaging). Builds release/Pagouro-BE/:

  PAGOURO-BE.bat            one-line launcher: PAGOURO-BE "a woman with a parasol"  -> workspace/art/<time>.png
  sd/                       stable-diffusion.cpp CPU build (sd-cli.exe + ggml DLLs), unchanged upstream binaries
  model/pagouro-be-1.0-f16.gguf
  README.md, CORPUS.md, CHECK_YOUR_COPY.md, THREAT_MODEL.md, LICENSES.md, facts.json
  ledger/                   the training-set ledger and every source ledger with its captions
  evals/                    gate40.jsonl, verdicts, summaries, the human samples
  MANIFEST.md               path | sha256 | size for every file (verify_manifest.py / VERIFY.bat check it)
  verify_manifest.py, verify_manifest.ps1, VERIFY.bat  (from Pagouro; the .py also accepts pagouro.pub)
  pagouro.pub               the release signing key (same key as Pagouro)

    python scripts/package_be.py --model runs/round3/pagouro-be-r3-f16.gguf --version 1.0
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
BE = os.path.dirname(HERE)
BUILD = os.path.abspath(os.path.join(BE, "..", "PAGOURO_BUILD"))
DATA = os.path.join(BUILD, "data", "images")

BAT = r"""@echo off
REM Pagouro BE — draws a Belle Époque poster from a sentence, on your CPU, offline.
REM   PAGOURO-BE "a woman in a long dress holding a parasol"
REM   PAGOURO-BE "a black cat" 20 1234      (steps, seed; defaults 20 and random)
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: PAGOURO-BE "what to draw" [steps] [seed]
  echo Example: PAGOURO-BE "a lighthouse on a rocky coast at dusk"
  exit /b 1
)
set STEPS=%~2
if "%STEPS%"=="" set STEPS=20
set SEED=%~3
if "%SEED%"=="" set SEED=-1
if not exist workspace\art mkdir workspace\art
for /f "tokens=1-3 delims=/: " %%a in ("%time%") do set T=%%a%%b%%c
set OUT=workspace\art\%date:~-4%%date:~-10,2%%date:~-7,2%-%T: =0%.png
echo Drawing "%~1" (%STEPS% steps) ... a few minutes on a laptop; the PNG lands in workspace\art\
sd\sd-cli.exe -m model\pagouro-be-1.0-f16.gguf -p "belleposter, Belle Epoque lithograph poster, %~1" -n "photograph, photo, realistic, 3d render, blurry, watermark, modern, gradient" --steps %STEPS% --cfg-scale 7 -W 512 -H 512 -s %SEED% -o "%OUT%" -v 2>nul | findstr /i "sampling completed"
if exist "%OUT%" (echo Saved %OUT%) else (echo Nothing was drawn. Run with -v to see why: sd\sd-cli.exe --help)
endlocal
"""

CHECK = """# Check your copy (Pagouro BE)

The same three steps as Pagouro's `CHECK_YOUR_COPY.md`, on this folder:

1. **Every file matches the manifest.** Double-click `VERIFY.bat` (Windows, nothing to install), or run
   `python verify_manifest.py`. It must end with *every listed file matches the manifest*.
2. **The manifest is signed.** `minisign -Vm MANIFEST.md -p pagouro.pub` (the same key as Pagouro, printed
   in both READMEs: `RWQe8tvI6RCE2uMbuILC9/rEr6bNZdcOA+WC7dHtObLE94ovGk8xuFlG`).
3. **The manifest existed on the release date.** `MANIFEST.md.ots` beside it is an OpenTimestamps proof;
   `ots info MANIFEST.md.ots` shows the Bitcoin block.

If step 1 fails, this is not a Pagouro BE. If it passes, every byte of the model and the runtime is the one
that was measured.
"""

LICENSES = """# Licences (Pagouro BE)

- **Model weights** (`model/pagouro-be-1.0-f16.gguf`): CC-BY-SA-4.0. They are a fine-tune of CommonCanvas-S-C
  (CC-BY-SA-4.0, Mosaic / Cornell, https://huggingface.co/common-canvas/CommonCanvas-S-C), so the
  share-alike travels with them; attribution: "CommonCanvas-S-C by the CommonCanvas authors; fine-tuned by
  Eric Wade, with Claude (Anthropic), on public-domain posters — see CORPUS.md".
- **Training images**: public domain (Library of Congress, no known restrictions; The Met Open Access CC0;
  Art Institute of Chicago CC0). Each one's row is in `ledger/`.
- **Runtime** (`sd/`): stable-diffusion.cpp and ggml, MIT, unchanged binaries from the upstream release
  named in `facts.json`.
- **Scripts and documents in this folder**: Apache 2.0 (code) and CC BY-SA 4.0 (documents).
- **What it draws for you**: CC0. No watermark. The project claims no rights in the pictures.
"""


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--out", default=os.path.join(BE, "release", "Pagouro-BE"))
    a = ap.parse_args()
    out = a.out
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    # runtime
    for fn in os.listdir(os.path.join(BE, "tools", "sdcpp")):
        if fn.endswith((".exe", ".dll", ".txt", ".md")) and "server" not in fn:
            copy(os.path.join(BE, "tools", "sdcpp", fn), os.path.join(out, "sd", fn))
    # model
    copy(a.model, os.path.join(out, "model", f"pagouro-be-{a.version}-f16.gguf"))
    # launcher + docs
    io.open(os.path.join(out, "PAGOURO-BE.bat"), "w", encoding="ascii", newline="\r\n").write(BAT)
    io.open(os.path.join(out, "CHECK_YOUR_COPY.md"), "w", encoding="utf-8", newline="\n").write(CHECK)
    io.open(os.path.join(out, "LICENSES.md"), "w", encoding="utf-8", newline="\n").write(LICENSES)
    for fn in ("README.md",):
        copy(os.path.join(BE, fn), os.path.join(out, fn))
    copy(os.path.join(BE, "docs", "CORPUS.md"), os.path.join(out, "CORPUS.md"))
    copy(os.path.join(BUILD, "docs", "THREAT_MODEL.md"), os.path.join(out, "THREAT_MODEL.md"))
    for fn in ("verify_manifest.py", "verify_manifest.ps1", "VERIFY.bat"):
        copy(os.path.join(BUILD, "scripts", fn), os.path.join(out, fn))
    copy(os.path.join(BUILD, "release", "Pagouro", "pagouro.pub"), os.path.join(out, "pagouro.pub"))
    if os.path.exists(os.path.join(BE, "docs", "facts.json")):
        copy(os.path.join(BE, "docs", "facts.json"), os.path.join(out, "facts.json"))
    # ledgers
    for src, dst in (("be_train_r3/ledger.jsonl", "ledger/training_set.jsonl"),
                     ("loc/ledger.jsonl", "ledger/loc.jsonl"), ("loc/ledger.jsonl.captions.jsonl", "ledger/loc.captions.jsonl"),
                     ("aic/ledger.jsonl", "ledger/aic.jsonl"), ("aic/ledger.jsonl.captions.jsonl", "ledger/aic.captions.jsonl"),
                     ("met_curated.jsonl", "ledger/met.jsonl"), ("met_curated.jsonl.captions.jsonl", "ledger/met.captions.jsonl"),
                     ("ledger.jsonl", "ledger/met_pool.jsonl")):
        p = os.path.join(DATA, src)
        if os.path.exists(p):
            copy(p, os.path.join(out, dst))
    # evals
    copy(os.path.join(BE, "evals", "gate40.jsonl"), os.path.join(out, "evals", "gate40.jsonl"))
    for r in ("round1", "round2", "round3"):
        d = os.path.join(BE, "evals", "results", r)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith((".md", ".jsonl", ".jpg", ".png")) and not fn.endswith(".log"):
                copy(os.path.join(d, fn), os.path.join(out, "evals", r, fn))
            if fn == "human_sample":
                for hf in os.listdir(os.path.join(d, fn)):
                    if hf.endswith((".json",)) and "b64" not in hf:
                        copy(os.path.join(d, fn, hf), os.path.join(out, "evals", r, "human_sample", hf))
    os.makedirs(os.path.join(out, "workspace", "art"), exist_ok=True)
    io.open(os.path.join(out, "workspace", "README.txt"), "w", encoding="utf-8", newline="\n").write(
        "Pictures you draw land in workspace/art/. Nothing else is ever written to this folder.\n")
    # manifest (same row format as Pagouro's, so verify_manifest.py works unchanged)
    rows = []
    for dirpath, _, files in os.walk(out):
        for fn in files:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, out).replace("\\", "/")
            if rel in ("MANIFEST.md", "MANIFEST.md.minisig", "MANIFEST.md.ots") or rel.startswith("workspace/"):
                continue
            rows.append((rel, sha256(p), os.path.getsize(p)))
    rows.sort()
    with io.open(os.path.join(out, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as m:
        m.write(f"# Pagouro BE {a.version} — manifest\n\nBuilt {time.strftime('%Y-%m-%d %H:%M')} local. {len(rows)} files. "
                "Every file on the stick with its SHA-256 and size; `verify_manifest.py` or `VERIFY.bat` checks them.\n\n")
        m.write("| file | sha256 | bytes |\n|---|---|---|\n")
        for rel, h, n in rows:
            m.write(f"| `{rel}` | `{h}` | {n:,} |\n")
    total = sum(n for _, _, n in rows)
    print(f"packaged {len(rows)} files, {total/1e9:.2f} GB -> {out}")
    print("manifest sha256", sha256(os.path.join(out, "MANIFEST.md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
