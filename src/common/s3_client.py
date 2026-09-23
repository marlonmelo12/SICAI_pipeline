# src/common/s3_client.py
"""
Cliente padronizado de Object Storage para o SICAI (Garage S3 e AWS S3).
"""
import os
from typing import Optional, Dict, Any
import boto3
from botocore.client import Config

class S3StorageClient:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "garage"
    ):
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL", "http://localhost:3900")
        self.access_key = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "sicai_access_key")
        self.secret_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY", "sicai_secret_key")
        self.region_name = region_name or os.getenv("AWS_DEFAULT_REGION", "garage")

        self.s3 = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
        )

    def ensure_bucket_exists(self, bucket_name: str):
        try:
            self.s3.head_bucket(Bucket=bucket_name)
        except Exception:
            self.s3.create_bucket(Bucket=bucket_name)

    def upload_file(self, local_path: str, bucket_name: str, object_key: str, metadata: Optional[Dict[str, str]] = None) -> str:
        extra_args = {}
        if metadata:
            extra_args["Metadata"] = metadata
        self.s3.upload_file(local_path, bucket_name, object_key, ExtraArgs=extra_args)
        return f"s3://{bucket_name}/{object_key}"

    def download_file(self, bucket_name: str, object_key: str, local_path: str):
        self.s3.download_file(bucket_name, object_key, local_path)
