"""Zip the stick folder with Python's zipfile (forward-slash paths; Windows PowerShell 5.1 Compress-Archive
writes backslashes, Pagouro erratum E3). Writes release/dist/Pagouro-BE-<v>-win64.zip and its .sha256,
and checks the archive lists no backslash paths.

    python scripts/zip_release.py --version 1.0
"""
from __future__ import annotations
import argparse, hashlib, os, sys, zipfile

BE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="1.0")
    a = ap.parse_args()
    src = os.path.join(BE, "release", f"Pagouro-BE-{a.version}")
    dist = os.path.join(BE, "release", "dist")
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, f"Pagouro-BE-{a.version}-win64.zip")
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dirpath, dirs, files in os.walk(src):
            dirs.sort()
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                arc = "Pagouro-BE/" + os.path.relpath(p, src).replace(os.sep, "/")
                z.write(p, arc, compress_type=zipfile.ZIP_STORED if fn.endswith((".gguf", ".png", ".jpg")) else zipfile.ZIP_DEFLATED)
                n += 1
    with zipfile.ZipFile(out) as z:
        bad = [i.filename for i in z.infolist() if "\\" in i.filename]
        assert not bad, bad[:3]
        assert z.testzip() is None
    h = hashlib.sha256()
    with open(out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    open(out + ".sha256", "w").write(h.hexdigest() + "\n")
    print(f"{n} files -> {out} {os.path.getsize(out):,} B sha256 {h.hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
