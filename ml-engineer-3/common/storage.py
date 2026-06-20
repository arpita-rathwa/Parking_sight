"""Storage abstraction: one interface, two backends.

  * local : plain filesystem under LOCAL_STORAGE_DIR (demo, zero AWS)
  * s3    : boto3 against real S3 or MinIO (S3_ENDPOINT_URL)

Production swap is a single env var (STORAGE_BACKEND=s3). The rest of the
codebase never imports boto3 directly — it only talks to Storage.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from common.config import get_settings


class Storage:
    def __init__(self) -> None:
        self.s = get_settings()
        self.backend = self.s.storage_backend
        if self.backend == "s3":
            import boto3  # lazy: only needed in s3 mode

            self._s3 = boto3.client(
                "s3",
                endpoint_url=self.s.s3_endpoint_url,
                region_name=self.s.aws_region,
            )
        else:
            Path(self.s.local_storage_dir).mkdir(parents=True, exist_ok=True)

    # ---- path helpers -----------------------------------------------------
    def _local_path(self, bucket: str, key: str) -> Path:
        return Path(self.s.local_storage_dir) / bucket / key

    # ---- bytes ------------------------------------------------------------
    def put_bytes(self, bucket: str, key: str, data: bytes) -> str:
        if self.backend == "s3":
            self._s3.put_object(Bucket=bucket, Key=key, Body=data)
        else:
            p = self._local_path(bucket, key)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        return self.uri(bucket, key)

    def get_bytes(self, bucket: str, key: str) -> bytes:
        if self.backend == "s3":
            return self._s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        return self._local_path(bucket, key).read_bytes()

    # ---- files ------------------------------------------------------------
    def put_file(self, bucket: str, key: str, local_file: str | Path) -> str:
        if self.backend == "s3":
            self._s3.upload_file(str(local_file), bucket, key)
        else:
            dest = self._local_path(bucket, key)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_file, dest)
        return self.uri(bucket, key)

    def get_file(self, bucket: str, key: str, local_file: str | Path) -> Path:
        Path(local_file).parent.mkdir(parents=True, exist_ok=True)
        if self.backend == "s3":
            self._s3.download_file(bucket, key, str(local_file))
        else:
            shutil.copy2(self._local_path(bucket, key), local_file)
        return Path(local_file)

    # ---- json convenience -------------------------------------------------
    def put_json(self, bucket: str, key: str, obj) -> str:
        return self.put_bytes(bucket, key, json.dumps(obj, indent=2, default=str).encode())

    def get_json(self, bucket: str, key: str):
        return json.loads(self.get_bytes(bucket, key).decode())

    # ---- listing / existence ---------------------------------------------
    def list(self, bucket: str, prefix: str = "") -> list[str]:
        if self.backend == "s3":
            keys, token = [], None
            while True:
                kw = {"Bucket": bucket, "Prefix": prefix}
                if token:
                    kw["ContinuationToken"] = token
                resp = self._s3.list_objects_v2(**kw)
                keys += [o["Key"] for o in resp.get("Contents", [])]
                if not resp.get("IsTruncated"):
                    break
                token = resp["NextContinuationToken"]
            return keys
        base = self._local_path(bucket, prefix)
        root = Path(self.s.local_storage_dir) / bucket
        if not base.exists():
            # prefix may be a partial path; walk the bucket and filter
            if not root.exists():
                return []
            return [
                str(p.relative_to(root))
                for p in root.rglob("*")
                if p.is_file() and str(p.relative_to(root)).startswith(prefix)
            ]
        return [str(p.relative_to(root)) for p in base.rglob("*") if p.is_file()]

    def exists(self, bucket: str, key: str) -> bool:
        if self.backend == "s3":
            try:
                self._s3.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                return False
        return self._local_path(bucket, key).exists()

    def uri(self, bucket: str, key: str) -> str:
        if self.backend == "s3":
            return f"s3://{bucket}/{key}"
        return f"file://{os.path.abspath(self._local_path(bucket, key))}"
