"""Mirror on Quilibrium QStorage (S3-compatible; D-40 mirror). Reads the Access Key ID / Secret Access Key
from PAGOURO_BUILD/.env (lines "Access Key ID: …" / "Secret Access Key: …" or with '='), never prints them.
Creates the bucket if needed, uploads the given files with public-read where the service allows it, and
prints the object URLs it then verifies by an unauthenticated GET (HEAD) — the honest test of "public".

    python scripts/qstorage_mirror.py --bucket pagouro --files site/index.html:index.html docs/MANIFEST_v1.0.md:be/MANIFEST_v1.0.md ...
    python scripts/qstorage_mirror.py --bucket pagouro --list
"""
from __future__ import annotations
import argparse, io, mimetypes, os, re, sys, urllib.request

BE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(BE, "..", "PAGOURO_BUILD", ".env")
ENDPOINT = "https://qstorage.quilibrium.com"


def creds():
    ak = sk = None
    for line in io.open(ENV, encoding="utf-8"):
        m = re.match(r"^\s*Access Key ID\s*[:=]\s*(\S+)", line)
        if m:
            ak = m.group(1)
        m = re.match(r"^\s*Secret Access Key\s*[:=]\s*(\S+)", line)
        if m:
            sk = m.group(1)
    if not (ak and sk):
        raise SystemExit("QStorage credentials not found in .env")
    return ak, sk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default="pagouro")
    ap.add_argument("--files", nargs="*", default=[], help="local:remote pairs")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-acl", action="store_true")
    a = ap.parse_args()
    import boto3
    from botocore.config import Config
    ak, sk = creds()
    # boto3 >= 1.36 adds a CRC32 checksum trailer to every PutObject; QStorage answers AccessDenied to it
    # (not a permissions problem). Multipart, copy and tagging worked all along; this switches the trailer off.
    s3 = boto3.client("s3", endpoint_url=ENDPOINT, aws_access_key_id=ak, aws_secret_access_key=sk,
                      region_name="q-world-1", config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 4},
                                                             request_checksum_calculation="when_required",
                                                             response_checksum_validation="when_required"))
    names = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    print("buckets:", names)
    if a.bucket not in names:
        s3.create_bucket(Bucket=a.bucket)
        print("created", a.bucket)
    if a.list:
        r = s3.list_objects_v2(Bucket=a.bucket)
        for o in r.get("Contents", []):
            print(f"  {o['Size']:>12,}  {o['Key']}")
        return 0
    for pair in a.files:
        local, remote = pair.split(":", 1)
        ctype = mimetypes.guess_type(remote)[0] or "application/octet-stream"
        extra = {"ContentType": ctype}
        if not a.no_acl:
            extra["ACL"] = "public-read"
        size = os.path.getsize(local)
        print(f"upload {remote} ({size:,} B, {ctype})", flush=True)
        try:
            s3.upload_file(local, a.bucket, remote, ExtraArgs=extra)
        except Exception as e:  # noqa: BLE001
            if "ACL" in extra:
                print("  ACL refused, retrying without:", str(e)[:100])
                extra.pop("ACL")
                s3.upload_file(local, a.bucket, remote, ExtraArgs=extra)
            else:
                raise
        url = f"{ENDPOINT}/{a.bucket}/{remote}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"  public HEAD {r.status} {url}")
        except Exception as e:  # noqa: BLE001
            print(f"  not public without auth: {str(e)[:80]}  ({url})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
