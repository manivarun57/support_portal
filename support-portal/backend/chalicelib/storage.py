import base64
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from chalicelib.logger import log_error, log_info


class StorageClient:
    """
    Simple wrapper that can push files to S3 or a local folder when running offline.
    """

    def __init__(self) -> None:
        self.bucket = os.getenv("S3_BUCKET_NAME", "support-portal-uploads")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.offline = os.getenv("AWS_OFFLINE", "true").lower() == "true"
        self._local_root = Path(__file__).resolve().parent.parent / "tmp" / "s3"
        try:
            if not self.offline:
                self._client = boto3.client("s3", region_name=self.region)
                log_info(
                    "Initialized S3 client",
                    bucket=self.bucket,
                    region=self.region,
                )
            else:
                self._client = None
                self._local_root.mkdir(parents=True, exist_ok=True)
                log_info("Using local filesystem for attachments", path=str(self._local_root))
        except Exception as exc:  # pragma: no cover - defensive
            log_error("Failed to initialize storage client", error=str(exc))
            raise

    def store_base64_blob(
        self, blob: str, filename: str, content_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Persist a Base64 encoded payload and return a tuple of (url, key).
        """
        key = f"tickets/{uuid.uuid4()}-{filename}"
        try:
            data = base64.b64decode(blob.split(",")[-1])
            log_info("Decoded attachment payload", key=key)
        except Exception as exc:  # pragma: no cover - sanity
            log_error("Failed to decode attachment payload", error=str(exc))
            raise

        if self.offline:
            return self._store_locally(data, key)

        return self._store_in_s3(data, key, content_type)

    def _store_locally(self, data: bytes, key: str) -> Tuple[str, str]:
        try:
            target_path = self._local_root / key
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(data)
            url = f"http://localhost/mock-s3/{key}".replace("\\", "/")
            log_info("Stored attachment locally", path=str(target_path))
            return url, key
        except OSError as exc:
            log_error("Local file write failed", error=str(exc), path=str(target_path))
            raise

    def _store_in_s3(
        self, data: bytes, key: str, content_type: Optional[str]
    ) -> Tuple[str, str]:
        extra_args = {"Bucket": self.bucket, "Key": key, "Body": data}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self._client.put_object(**extra_args)
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            log_info("Uploaded attachment to S3", key=key, bucket=self.bucket)
            return url, key
        except (BotoCoreError, ClientError) as exc:
            log_error("S3 upload failed", error=str(exc), key=key, bucket=self.bucket)
            raise

