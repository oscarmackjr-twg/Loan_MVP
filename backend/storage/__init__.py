"""Storage abstraction layer for file operations."""
from .base import StorageBackend, StorageType
from .factory import get_storage_backend

__all__ = ["StorageBackend", "StorageType", "get_storage_backend"]
