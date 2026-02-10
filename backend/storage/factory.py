"""Storage backend factory."""
from typing import Optional
from config.settings import settings
from .base import StorageBackend, StorageType
from .local import LocalStorageBackend
from .s3 import S3StorageBackend


def get_storage_backend(
    storage_type: Optional[str] = None,
    base_path: Optional[str] = None
) -> StorageBackend:
    """
    Get a storage backend instance based on configuration.
    
    Args:
        storage_type: Storage type ("local" or "s3"). If None, uses STORAGE_TYPE from settings.
        base_path: Base path/prefix for storage. If None, uses appropriate setting.
    
    Returns:
        StorageBackend instance
    """
    storage_type = storage_type or settings.STORAGE_TYPE
    
    if storage_type == StorageType.LOCAL:
        base_path = base_path or settings.INPUT_DIR
        return LocalStorageBackend(base_path=base_path)
    
    elif storage_type == StorageType.S3:
        if not settings.S3_BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME must be set when using S3 storage")
        
        # For IAM Identity Center organizations, credentials may not be provided
        # boto3 will use IAM role (ECS) or SSO credentials automatically
        return S3StorageBackend(
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.S3_REGION or "us-east-1",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,  # Optional - uses IAM role if None
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,  # Optional - uses IAM role if None
            base_prefix=base_path or settings.S3_BASE_PREFIX or ""
        )
    
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
