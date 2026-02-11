"""Storage backend factory."""
from __future__ import annotations

from typing import Optional

from config.settings import settings
from .base import StorageBackend, StorageType
from .local import LocalStorageBackend
from .s3 import S3StorageBackend


def _join_prefix(prefix: str, suffix: str) -> str:
    prefix = (prefix or "").strip("/")
    suffix = (suffix or "").strip("/")
    if not prefix:
        return suffix
    if not suffix:
        return prefix
    return f"{prefix}/{suffix}"


def get_storage_backend(
    storage_type: Optional[str] = None,
    *,
    area: str = "inputs",
    base_path: Optional[str] = None,
) -> StorageBackend:
    """
    Get a storage backend instance based on configuration.

    Args:
        storage_type: Storage type ("local" or "s3"). If None, uses STORAGE_TYPE from settings.
        area: Logical storage area: "inputs", "outputs", or "output_share".
        base_path: Override base path/prefix. For local it's a directory; for S3 it's a key prefix.

    Returns:
        StorageBackend instance
    """
    storage_type = storage_type or settings.STORAGE_TYPE

    if storage_type == StorageType.LOCAL:
        if base_path is None:
            if area == "outputs":
                base_path = settings.OUTPUT_DIR
            elif area == "output_share":
                base_path = settings.OUTPUT_SHARE_DIR
            else:
                base_path = settings.INPUT_DIR
        return LocalStorageBackend(base_path=base_path)

    if storage_type == StorageType.S3:
        if not settings.S3_BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME must be set when using S3 storage")

        # Default S3 prefix: <S3_BASE_PREFIX>/<area>
        if base_path is None:
            base_path = _join_prefix(settings.S3_BASE_PREFIX or "", area)

        # For IAM Identity Center organizations, credentials may not be provided.
        # boto3 will use IAM role (ECS) or SSO credentials automatically.
        return S3StorageBackend(
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.S3_REGION or "us-east-1",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,  # optional
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,  # optional
            base_prefix=base_path,
        )

    raise ValueError(f"Unknown storage type: {storage_type}")
