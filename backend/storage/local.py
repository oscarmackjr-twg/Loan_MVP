"""Local filesystem storage backend."""
import os
from pathlib import Path
from typing import List
from datetime import datetime
from .base import StorageBackend, FileInfo


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: str = "./data"):
        """
        Initialize local storage backend.
        
        Args:
            base_path: Base directory for all file operations
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a relative path to an absolute path within base_path."""
        # Normalize path separators and remove leading slashes
        normalized = path.replace("\\", "/").lstrip("/")
        resolved = self.base_path / normalized
        # Prevent directory traversal
        try:
            resolved = resolved.resolve()
            if not str(resolved).startswith(str(self.base_path.resolve())):
                raise ValueError(f"Path {path} is outside base directory")
        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid path: {path}") from e
        return resolved
    
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        return file_path.read_bytes()
    
    def write_file(self, path: str, content: bytes) -> None:
        """Write bytes to a file."""
        file_path = self._resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
    
    def delete_file(self, path: str) -> None:
        """Delete a file."""
        file_path = self._resolve_path(path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
        elif file_path.exists() and file_path.is_dir():
            raise ValueError(f"Cannot delete directory with delete_file: {path}")
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        file_path = self._resolve_path(path)
        return file_path.exists() and file_path.is_file()
    
    def list_files(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List files in a directory."""
        dir_path = self._resolve_path(path)
        if not dir_path.exists():
            return []
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        files = []
        if recursive:
            for item in dir_path.rglob("*"):
                if item.is_file():
                    stat = item.stat()
                    files.append(FileInfo(
                        path=str(item.relative_to(self.base_path)),
                        size=stat.st_size,
                        is_directory=False,
                        last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
                    ))
        else:
            for item in dir_path.iterdir():
                stat = item.stat()
                files.append(FileInfo(
                    path=str(item.relative_to(self.base_path)),
                    size=stat.st_size if item.is_file() else 0,
                    is_directory=item.is_dir(),
                    last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
                ))
        
        return files
    
    def create_directory(self, path: str) -> None:
        """Create a directory (if it doesn't exist)."""
        dir_path = self._resolve_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a URL to access/download a file (for local, returns file:// path)."""
        file_path = self._resolve_path(path)
        return f"file://{file_path.as_uri()}"
