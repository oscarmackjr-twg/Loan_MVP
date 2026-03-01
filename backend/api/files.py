"""File management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from storage import get_storage_backend
from auth.security import get_current_user
from db.models import User
from config.settings import settings
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/list")
async def list_files(
    path: str = Query("", description="Directory path to list"),
    recursive: bool = Query(False, description="List files recursively"),
    area: str = Query("inputs", description="Storage area: inputs | outputs | output_share"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """List files in a directory."""
    try:
        storage = get_storage_backend(storage_type=storage_type, area=area)
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
    area: str = Query("inputs", description="Storage area: inputs | outputs | output_share"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Upload a file. When using S3, uploads always go to the inputs area so the pipeline can read them."""
    try:
        # Per spec: dropped files must land in the input directory. When S3 is used, force inputs area.
        effective_area = area
        if (storage_type or settings.STORAGE_TYPE) == "s3":
            effective_area = "inputs"
        storage = get_storage_backend(storage_type=storage_type, area=effective_area)
        
        # When S3, default path so files drop into inputs root: bucket/input/files_required/ (path "files_required/" under inputs area)
        effective_path = (path or "").strip()
        if (storage_type or settings.STORAGE_TYPE) == "s3" and not effective_path:
            effective_path = "files_required/"
        
        # Determine destination path
        if effective_path and not effective_path.endswith("/"):
            # If path doesn't end with /, treat as full file path
            dest_path = effective_path
        else:
            # Use filename in the specified directory
            dest_path = f"{effective_path.rstrip('/')}/{file.filename}" if effective_path else file.filename
        
        # Read file content
        content = await file.read()
        
        # Write to storage
        storage.write_file(dest_path, content)
        
        return {
            "message": "File uploaded successfully",
            "path": dest_path,
            "size": len(content)
        }
    except ValueError as e:
        # S3 NoSuchBucket or other clear config errors
        logger.error("Upload error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        detail = str(e)
        if "NoSuchBucket" in detail or "bucket" in detail.lower():
            if getattr(settings, "S3_BUCKET_NAME", None):
                detail = f"{detail} (Configured bucket: {settings.S3_BUCKET_NAME}. Create it in S3 or set S3_BUCKET_NAME to an existing bucket.)"
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {detail}")


@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    area: str = Query("inputs", description="Storage area: inputs | outputs | output_share"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Download a file."""
    try:
        storage = get_storage_backend(storage_type=storage_type, area=area)
        
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
    area: str = Query("inputs", description="Storage area: inputs | outputs | output_share"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Get a presigned URL for file access (S3) or file path (local)."""
    try:
        storage = get_storage_backend(storage_type=storage_type, area=area)
        
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
    area: str = Query("inputs", description="Storage area: inputs | outputs | output_share"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Delete a file."""
    try:
        storage = get_storage_backend(storage_type=storage_type, area=area)
        
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
    area: str = Query("inputs", description="Storage area: inputs | outputs | output_share"),
    storage_type: Optional[str] = Query(None, description="Override storage type (local/s3)"),
    current_user: User = Depends(get_current_user)
):
    """Create a directory."""
    try:
        storage = get_storage_backend(storage_type=storage_type, area=area)
        storage.create_directory(path)
        
        return {"message": "Directory created successfully", "path": path}
    except Exception as e:
        logger.error(f"Error creating directory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")
