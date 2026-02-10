"""File management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
from storage import get_storage_backend, StorageType
from storage.base import FileInfo
from auth.routes import get_current_user
from db.models import User
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/list")
async def list_files(
    path: str = Query("", description="Directory path to list"),
    recursive: bool = Query(False, description="List files recursively"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """List files in a directory."""
    try:
        storage = get_storage_backend(storage_type=storage_type)
        files = storage.list_files(path or "", recursive=recursive)
        
        return {
            "path": path,
            "files": [
                {
                    "path": f.path,
                    "size": f.size,
                    "is_directory": f.is_directory,
                    "last_modified": f.last_modified
                }
                for f in files
            ]
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Query("", description="Destination path (directory or full file path)"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Upload a file."""
    try:
        storage = get_storage_backend(storage_type=storage_type)
        
        # Determine destination path
        if path and not path.endswith("/"):
            # If path doesn't end with /, treat as full file path
            dest_path = path
        else:
            # Use filename in the specified directory
            dest_path = f"{path.rstrip('/')}/{file.filename}" if path else file.filename
        
        # Read file content
        content = await file.read()
        
        # Write to storage
        storage.write_file(dest_path, content)
        
        return {
            "message": "File uploaded successfully",
            "path": dest_path,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Download a file."""
    try:
        storage = get_storage_backend(storage_type=storage_type)
        
        if not storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        content = storage.read_file(file_path)
        
        # Determine content type from file extension
        content_type = "application/octet-stream"
        if file_path.endswith(".csv"):
            content_type = "text/csv"
        elif file_path.endswith(".xlsx"):
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_path.endswith(".xls"):
            content_type = "application/vnd.ms-excel"
        elif file_path.endswith(".json"):
            content_type = "application/json"
        elif file_path.endswith(".txt"):
            content_type = "text/plain"
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_path.split("/")[-1]}"'
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error downloading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.get("/url/{file_path:path}")
async def get_file_url(
    file_path: str,
    expires_in: int = Query(3600, description="URL expiration time in seconds"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Get a presigned URL for file access (S3) or file path (local)."""
    try:
        storage = get_storage_backend(storage_type=storage_type)
        
        if not storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        url = storage.get_file_url(file_path, expires_in=expires_in)
        
        return {"url": url, "expires_in": expires_in}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error getting file URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get file URL: {str(e)}")


@router.delete("/{file_path:path}")
async def delete_file(
    file_path: str,
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Delete a file."""
    try:
        storage = get_storage_backend(storage_type=storage_type)
        
        if not storage.file_exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        storage.delete_file(file_path)
        
        return {"message": "File deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.post("/mkdir")
async def create_directory(
    path: str = Query(..., description="Directory path to create"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Create a directory."""
    try:
        storage = get_storage_backend(storage_type=storage_type)
        storage.create_directory(path)
        
        return {"message": "Directory created successfully", "path": path}
    except Exception as e:
        logger.error(f"Error creating directory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")
