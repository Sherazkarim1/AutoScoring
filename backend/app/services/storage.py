import mimetypes
import uuid
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings


class FileStorage:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir).resolve()
        self.bucket = settings.storage_bucket
        self.use_object_storage = all(
            (
                settings.aws_access_key_id,
                settings.aws_secret_access_key,
                settings.aws_endpoint_url_s3,
                settings.storage_bucket,
            )
        )
        if settings.render and not self.use_object_storage:
            raise RuntimeError(
                "Neon object storage credentials are required on Render. "
                "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_ENDPOINT_URL_S3."
            )
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.aws_endpoint_url_s3,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
                config=Config(s3={"addressing_style": "path"}),
            )
        return self._client

    def save(self, content: bytes, suffix: str) -> str:
        filename = f"{uuid.uuid4().hex}{suffix}"
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if self.use_object_storage:
            self.client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=content,
                ContentType=content_type,
            )
        else:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            (self.upload_dir / filename).write_bytes(content)
        return filename

    def read(self, filename: str) -> bytes:
        if Path(filename).name != filename:
            raise ValueError("Invalid filename")
        if self.use_object_storage:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=filename)
                return response["Body"].read()
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code")
                if code in {"NoSuchKey", "NoSuchBucket", "404"}:
                    raise FileNotFoundError(filename) from exc
                raise
        path = (self.upload_dir / filename).resolve()
        if not path.is_relative_to(self.upload_dir) or not path.is_file():
            raise FileNotFoundError(filename)
        return path.read_bytes()

    @staticmethod
    def media_type(filename: str) -> str:
        return mimetypes.guess_type(filename)[0] or "application/octet-stream"


@lru_cache
def get_file_storage() -> FileStorage:
    return FileStorage()
