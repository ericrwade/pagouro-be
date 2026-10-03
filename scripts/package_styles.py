"""Package Pagouro BE Styles 1.0 (D-103): a folder that drops into a Pagouro BE stick.

  Pagouro-BE-Styles-1.0/
    styles/<name>.safetensors        one LoRA per style (diffusers/PEFT format; stable-diffusion.cpp loads it)
    PAGOURO-BE-STYLE.bat             PAGOURO-BE-STYLE rockart "a black cat"  -> workspace\\art\\<time>.png
    STYLES.md                        per style: what it is, corpus and licences, gate numbers, recommended weight
    ledger/<name>.jsonl              the training-set ledger per style (source row, licence, attribution, crop, caption)
    evals/                           gate captions, verdicts, sheets
    README.md, LICENSES.md, MANIFEST.md (+ signature and timestamp added after)

    python scripts/package_styles.py --version 1.0 --weights rockart=0.8,greekvase=0.6,...
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); BE = os.path.dirname(HERE)
DATA = os.path.abspath(os.environ.get("PAGOURO_DATA") or os.path.join(BE, "..", "PAGOURO_BUILD", "data", "images"))

BAT = r"""@echo off
REM Pagouro BE Styles - draws in one of the pack's styles, on your CPU, offline. Needs a Pagouro BE folder:
REM put this folder's "styles" folder inside your Pagouro-BE folder (next to sd\ and model\), or run from there.
REM   PAGOURO-BE-STYLE rockart "a black cat sitting upright"
REM   PAGOURO-BE-STYLE ukiyoe "a lighthouse on a rocky coast" 20 1234      (steps, seed)
setlocal
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: PAGOURO-BE-STYLE ^<style^> "what to draw" [steps] [seed]
  echo Styles: __STYLES__
  exit /b 1
)
set STYLE=%~1
set STEPS=%~3
if "%STEPS%"=="" set STEPS=20
set SEED=%~4
if "%SEED%"=="" set SEED=-1
set BEDIR=.
if not exist sd\sd-cli.exe set BEDIR=..
if not exist %BEDIR%\sd\sd-cli.exe (
  echo Pagouro BE runtime not found. Put the styles folder inside your Pagouro-BE folder.
  exit /b 1
)
set PREFIX=
set W=
__CASES__
if "%PREFIX%"=="" (
  echo Unknown style "%STYLE%". Styles: __STYLES__
  exit /b 1
)
if not exist %BEDIR%\workspace\art mkdir %BEDIR%\workspace\art
for /f "tokens=1-3 delims=/: " %%a in ("%time%") do set T=%%a%%b%%c
set OUT=%BEDIR%\workspace\art\%STYLE%-%date:~-4%%date:~-10,2%%date:~-7,2%-%T: =0%.png
echo Drawing "%~2" in the %STYLE% style (%STEPS% steps) ...
%BEDIR%\sd\sd-cli.exe -m %BEDIR%\model\pagouro-be-1.0-f16.gguf --lora-model-dir "%~dp0styles" -p "%PREFIX%, %~2 <lora:%STYLE%:%W%>" -n "photograph, photo, 3d render, blurry, watermark, text, lettering, words, caption, title, modern, gradient" --steps %STEPS% --cfg-scale 7 -W 512 -H 512 -s %SEED% -o "%OUT%" -v 2>nul | findstr /i "sampling completed"
if exist "%OUT%" (echo Saved %OUT%) else (echo Nothing was drawn. Run sd\sd-cli.exe --help for details.)
endlocal
"""


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--weights", default="", help="style=weight,... recommended LoRA weights")
    ap.add_argument("--styles", nargs="*", default=None)
    ap.add_argument("--out", default=os.path.join(BE, "release", "Pagouro-BE-Styles-1.0"))
    a = ap.parse_args()
    styles = json.load(io.open(os.path.join(BE, "styles.json"), encoding="utf-8"))
    names = a.styles or [k for k in styles if not k.startswith("_")]
    weights = {k: 1.0 for k in names}
    for kv in filter(None, a.weights.split(",")):
        k, v = kv.split("="); weights[k] = float(v)
    out = a.out
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(os.path.join(out, "styles")); os.makedirs(os.path.join(out, "ledger")); os.makedirs(os.path.join(out, "evals"))
    rows = ["# Pagouro BE Styles " + a.version, "",
            "One LoRA file per style, trained on the shipped Pagouro BE model from a licensed, ledgered corpus, captioned by an",
            "open-weights vision model (Qwen 3.6 27B via OpenRouter; no commercial API in the chain). Numbers are from the frozen",
            "40-caption styles gate (`evals/gate40_styles.jsonl`), two seeds each, judged by a vision model with the strict rubric",
            "(`evals/summary.md`); the plain BE model on the same captions is the comparison line. **Faces and hands are measured,",
            "not promised**: no style passes the anatomy captions more often than about half the time.", "",
            "| style | trigger and phrase | recommended weight | corpus | subject | style match | anatomy ok | unasked lettering |",
            "|---|---|---|---|---|---|---|---|"]
    summ = {}
    for p in (os.path.join(BE, "runs", "styles", "summary.md"),):
        if os.path.exists(p):
            for line in io.open(p, encoding="utf-8"):
                if line.startswith("| ") and not line.startswith("| style") and not line.startswith("|---"):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]; summ[cells[0]] = cells
    for k in names:
        cfg = styles[k]
        src = os.path.join(BE, "runs", "styles", k, "lora", "pytorch_lora_weights.safetensors")
        shutil.copyfile(src, os.path.join(out, "styles", f"{k}.safetensors"))
        led = os.path.join(DATA, "styles_train", k, "ledger.jsonl")
        if os.path.exists(led): shutil.copyfile(led, os.path.join(out, "ledger", f"{k}.jsonl"))
        n = sum(1 for _ in io.open(led, encoding="utf-8")) if os.path.exists(led) else 0
        s = summ.get(k, ["", "", "?", "?", "?", "?"])
        rows.append(f"| {cfg['name']} (`{k}`) | `{cfg['trigger']}, {cfg['phrase']}` | {weights[k]} | {n} training files; see `ledger/{k}.jsonl` | {s[2]} | {s[3]} | {s[4]} | {s[5]} |")
        for extra in ("note",):
            if cfg.get(extra): rows.append(f"|  | {cfg[extra]} |  |  |  |  |  |  |")
    io.open(os.path.join(out, "STYLES.md"), "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
    cases = "\n".join(f'if /i "%STYLE%"=="{k}" (set "PREFIX={styles[k]["trigger"]}, {styles[k]["phrase"]}" & set W={weights[k]})' for k in names)
    bat = BAT.replace("__CASES__", cases).replace("__STYLES__", " ".join(names))
    io.open(os.path.join(out, "PAGOURO-BE-STYLE.bat"), "w", encoding="ascii", errors="replace", newline="\r\n").write(bat)
    # evals
    shutil.copyfile(os.path.join(BE, "evals", "gate40_styles.jsonl"), os.path.join(out, "evals", "gate40_styles.jsonl"))
    rs = os.path.join(BE, "runs", "styles")
    for fn in os.listdir(rs):
        if fn.startswith("verdicts_") or fn == "summary.md": shutil.copyfile(os.path.join(rs, fn), os.path.join(out, "evals", fn))
    for k in names:
        sh = os.path.join(rs, k, "sheet.jpg")
        if os.path.exists(sh): shutil.copyfile(sh, os.path.join(out, "evals", f"sheet_{k}.jpg"))
    shutil.copyfile(os.path.join(BE, "styles.json"), os.path.join(out, "styles.json"))
    for fn in ("README_STYLES.md", "LICENSES_STYLES.md"):
        p = os.path.join(BE, "docs", fn)
        if os.path.exists(p): shutil.copyfile(p, os.path.join(out, fn.replace("_STYLES", "")))
    # manifest
    entries = []
    for dirpath, _, files in os.walk(out):
        for fn in files:
            p = os.path.join(dirpath, fn); rel = os.path.relpath(p, out).replace("\\", "/")
            if rel in ("MANIFEST.md", "MANIFEST.md.minisig", "MANIFEST.md.ots"): continue
            entries.append((rel, sha256(p), os.path.getsize(p)))
    entries.sort()
    with io.open(os.path.join(out, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as m:
        m.write(f"# Pagouro BE Styles {a.version} — manifest\n\nBuilt {time.strftime('%Y-%m-%d %H:%M')} local. {len(entries)} files.\n\n| file | sha256 | bytes |\n|---|---|---|\n")
        for rel, h, n in entries: m.write(f"| `{rel}` | `{h}` | {n:,} |\n")
    print(f"packaged {len(entries)} files, {sum(n for _, _, n in entries)/1e6:.0f} MB -> {out}; manifest sha256 {sha256(os.path.join(out, 'MANIFEST.md'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
