"""AWS S3 storage backend."""
import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime
from .base import StorageBackend, FileInfo


class S3StorageBackend(StorageBackend):
    """AWS S3 storage implementation."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        base_prefix: str = ""
    ):
        """
        Initialize S3 storage backend.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            aws_access_key_id: AWS access key (optional, uses IAM role/SSO if not provided)
            aws_secret_access_key: AWS secret key (optional, uses IAM role/SSO if not provided)
            base_prefix: Prefix for all file paths (e.g., "inputs/" or "test/")
        
        Note: If credentials are not provided, boto3 will use:
        - IAM role (when running on ECS/EC2)
        - AWS SSO credentials (when using AWS_PROFILE)
        - Default credential chain
        """
        self.bucket_name = bucket_name
        self.region = region
        self.base_prefix = base_prefix.rstrip("/")
        
        # Initialize S3 client
        # If credentials are provided, use them; otherwise boto3 will use IAM role/SSO/default chain
        s3_kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            s3_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            })
        # If credentials not provided, boto3 will automatically use:
        # 1. IAM role (ECS/EC2 instance profile)
        # 2. AWS SSO credentials (if AWS_PROFILE is set)
        # 3. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 4. AWS credentials file (~/.aws/credentials)
        
        self.s3_client = boto3.client("s3", **s3_kwargs)
        self.s3_resource = boto3.resource("s3", **s3_kwargs)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path and add base prefix."""
        # Remove leading/trailing slashes and normalize
        normalized = path.replace("\\", "/").strip("/")
        if self.base_prefix:
            return f"{self.base_prefix}/{normalized}" if normalized else self.base_prefix
        return normalized
    
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        key = self._normalize_path(path)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File not found in S3: {path}")
            raise
    
    def write_file(self, path: str, content: bytes) -> None:
        """Write bytes to a file."""
        key = self._normalize_path(path)
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchBucket":
                raise ValueError(
                    f"S3 bucket '{self.bucket_name}' does not exist (region: {self.region}). "
                    "Create the bucket in AWS S3 or set S3_BUCKET_NAME to an existing bucket."
                ) from e
            raise
    
    def delete_file(self, path: str) -> None:
        """Delete a file."""
        key = self._normalize_path(path)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError:
            pass  # Ignore if file doesn't exist
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        key = self._normalize_path(path)
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            return error_code != "404"
    
    def list_files(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List files in a directory."""
        prefix = self._normalize_path(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        
        files = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        paginate_kwargs = {"Bucket": self.bucket_name, "Prefix": prefix}
        if not recursive:
            paginate_kwargs["Delimiter"] = "/"
        try:
            for page in paginator.paginate(**paginate_kwargs):
                # List "directories" (common prefixes)
                if "CommonPrefixes" in page:
                    for prefix_info in page["CommonPrefixes"]:
                        dir_path = prefix_info["Prefix"][len(self.base_prefix) + 1:] if self.base_prefix else prefix_info["Prefix"]
                        files.append(FileInfo(
                            path=dir_path.rstrip("/"),
                            size=0,
                            is_directory=True,
                            last_modified=None
                        ))
                
                # List files
                if "Contents" in page:
                    for obj in page["Contents"]:
                        # Skip the directory marker itself
                        if obj["Key"].endswith("/") and obj["Size"] == 0:
                            continue
                        
                        file_path = obj["Key"][len(self.base_prefix) + 1:] if self.base_prefix else obj["Key"]
                        files.append(FileInfo(
                            path=file_path,
                            size=obj["Size"],
                            is_directory=False,
                            last_modified=obj["LastModified"].isoformat() if "LastModified" in obj else None
                        ))
        except ClientError:
            pass  # Return empty list if bucket/prefix doesn't exist
        
        return files
    
    def create_directory(self, path: str) -> None:
        """Create a directory (S3 doesn't have directories, but we can create a marker object)."""
        # S3 doesn't have directories, but we can create an empty object with trailing /
        key = self._normalize_path(path)
        if not key.endswith("/"):
            key += "/"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=b"")
    
    def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a presigned URL to access/download a file."""
        key = self._normalize_path(path)
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise ValueError(f"Failed to generate presigned URL: {e}")
