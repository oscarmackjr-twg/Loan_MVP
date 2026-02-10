"""Base storage interface and types."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import BinaryIO, List, Optional
from pathlib import Path
import io


class StorageType(str, Enum):
    """Storage backend type."""
    LOCAL = "local"
    S3 = "s3"


class FileInfo:
    """File metadata."""
    def __init__(
        self,
        path: str,
        size: int,
        is_directory: bool = False,
        last_modified: Optional[str] = None
    ):
        self.path = path
        self.size = size
        self.is_directory = is_directory
        self.last_modified = last_modified


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        pass
    
    @abstractmethod
    def write_file(self, path: str, content: bytes) -> None:
        """Write bytes to a file."""
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> None:
        """Delete a file."""
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass
    
    @abstractmethod
    def list_files(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List files in a directory."""
        pass
    
    @abstractmethod
    def create_directory(self, path: str) -> None:
        """Create a directory (if it doesn't exist)."""
        pass
    
    @abstractmethod
    def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a URL to access/download a file (presigned URL for S3)."""
        pass
    
    def read_file_as_stream(self, path: str) -> BinaryIO:
        """Read a file as a stream (default implementation uses read_file)."""
        return io.BytesIO(self.read_file(path))
    
    def write_file_from_stream(self, path: str, stream: BinaryIO) -> None:
        """Write a file from a stream (default implementation reads entire stream)."""
        content = stream.read()
        self.write_file(path, content)
