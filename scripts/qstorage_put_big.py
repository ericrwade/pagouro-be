"""Upload one big file to QStorage by manual multipart with per-part retries (the transfer manager gave an
SSL EOF on a 128 MB part and an InvalidPart on completion). 32 MB parts, sequential, each part retried up to
6 times on any error, then CompleteMultipartUpload with the ETags the store returned.

    python scripts/qstorage_put_big.py <local file> <bucket key>
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qstorage_mirror import creds, ENDPOINT
import boto3
from botocore.config import Config

PART = 32 * 1024 * 1024


def main():
    src, key = sys.argv[1], sys.argv[2]
    ak, sk = creds()
    s3 = boto3.client("s3", endpoint_url=ENDPOINT, aws_access_key_id=ak, aws_secret_access_key=sk, region_name="q-world-1",
                      config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 3}, read_timeout=300, connect_timeout=60,
                                    request_checksum_calculation="when_required", response_checksum_validation="when_required"))
    for u in s3.list_multipart_uploads(Bucket="pagouro").get("Uploads", []):
        if u["Key"] == key:
            s3.abort_multipart_upload(Bucket="pagouro", Key=key, UploadId=u["UploadId"]); print("aborted leftover upload")
    size = os.path.getsize(src)
    ctype = "application/zip" if key.endswith(".zip") else "application/octet-stream"
    up = s3.create_multipart_upload(Bucket="pagouro", Key=key, ContentType=ctype, ACL="public-read")
    uid = up["UploadId"]
    parts = []
    n = 0
    t0 = time.time()
    with open(src, "rb") as f:
        while True:
            chunk = f.read(PART)
            if not chunk:
                break
            n += 1
            for attempt in range(1, 7):
                try:
                    r = s3.upload_part(Bucket="pagouro", Key=key, UploadId=uid, PartNumber=n, Body=chunk)
                    parts.append({"PartNumber": n, "ETag": r["ETag"]})
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"  part {n} attempt {attempt} failed: {str(e)[:90]}", flush=True)
                    time.sleep(5 * attempt)
            else:
                s3.abort_multipart_upload(Bucket="pagouro", Key=key, UploadId=uid)
                raise SystemExit(f"part {n} failed 6 times; aborted")
            if n % 10 == 0:
                print(f"  {n} parts, {n * PART / 1e9:.2f} GB, {time.time() - t0:,.0f}s", flush=True)
    s3.complete_multipart_upload(Bucket="pagouro", Key=key, UploadId=uid, MultipartUpload={"Parts": parts})
    head = s3.head_object(Bucket="pagouro", Key=key)
    print(f"done: {key} {n} parts; local {size:,} B, stored {head['ContentLength']:,} B, {time.time() - t0:,.0f}s", flush=True)
    return 0 if head["ContentLength"] == size else 1


if __name__ == "__main__":
    sys.exit(main())
