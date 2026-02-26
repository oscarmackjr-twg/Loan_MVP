Task: Implement File Management \& Storage Backends for the Loan Engine API



You are extending the Loan Engine application (Phases 0-2 complete) with fully

functional file management endpoints and production-ready storage backends.

After this phase, users can upload loan tape files, browse directories, download

outputs, and the system seamlessly switches between local filesystem and S3

based on configuration.





Context: What Already Exists (from Phases 0-2)



These files exist with working code. Do NOT regenerate them.

Import from these modules freely.



backend/config.py — Settings



python

class Settings(BaseSettings):

&nbsp;   APP\_NAME: str = "loan-engine"

&nbsp;   ENVIRONMENT: str = "development"

&nbsp;   DEBUG: bool = True

&nbsp;   DATABASE\_URL: str = "postgresql+asyncpg://..."

&nbsp;   SECRET\_KEY: str

&nbsp;   STORAGE\_TYPE: str = "local"          # "local" | "s3"

&nbsp;   LOCAL\_STORAGE\_PATH: str = "./storage"

&nbsp;   S3\_BUCKET\_NAME: str = ""

&nbsp;   S3\_REGION: str = "us-east-1"

&nbsp;   AWS\_ACCESS\_KEY\_ID: str = ""

&nbsp;   AWS\_SECRET\_ACCESS\_KEY: str = ""



backend/storage/base.py — Abstract Storage Backend (EXISTS, DO NOT MODIFY)



python

from abc import ABC, abstractmethod

from fastapi import UploadFile

from fastapi.responses import StreamingResponse



class StorageBackend(ABC):

&nbsp;   @abstractmethod

&nbsp;   async def list\_files(self, path: str, recursive: bool = False, area: str = "inputs") -> list\[dict]:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def upload\_file(self, file: UploadFile, destination: str, area: str = "inputs") -> dict:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def download\_file(self, path: str, area: str = "inputs") -> StreamingResponse:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def delete\_file(self, path: str, area: str = "inputs") -> dict:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def create\_directory(self, path: str, area: str = "inputs") -> dict:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def get\_presigned\_url(self, path: str, expires\_in: int = 3600, area: str = "inputs") -> str:

&nbsp;       ...



backend/api/dependencies.py — Storage Dependency (EXISTS from Phase 2)



python

from functools import lru\_cache

from backend.config import get\_settings

from backend.storage.base import StorageBackend

from backend.storage.local import LocalStorage

from backend.storage.s3 import S3Storage



@lru\_cache

def get\_storage() -> StorageBackend:

&nbsp;   settings = get\_settings()

&nbsp;   if settings.STORAGE\_TYPE == "s3":

&nbsp;       return S3Storage(

&nbsp;           bucket\_name=settings.S3\_BUCKET\_NAME,

&nbsp;           region=settings.S3\_REGION,

&nbsp;           aws\_access\_key\_id=settings.AWS\_ACCESS\_KEY\_ID,

&nbsp;           aws\_secret\_access\_key=settings.AWS\_SECRET\_ACCESS\_KEY,

&nbsp;       )

&nbsp;   else:

&nbsp;       return LocalStorage(base\_path=settings.LOCAL\_STORAGE\_PATH)



backend/auth/security.py — Auth Dependencies (EXISTS)



python

async def get\_current\_user(token, db) -> User      # requires valid JWT

async def admin\_required(current\_user) -> User      # requires admin role



backend/utils/path\_utils.py — Path Utilities (EXISTS, may be stub)



This file may be a stub from Phase 0. Replace with full implementation.



Pipeline usage of storage (Phase 2, for reference)



The pipeline engine already calls these storage methods:

• storage.list\_files(path, area="inputs") — to discover loan tape files

• storage.upload\_file(upload, destination, area="outputs") — to write notebook outputs

• storage.list\_files(run\_id, area="outputs") — to list notebook output files

• storage.download\_file(path, area="outputs") — to serve output downloads



Your storage implementations MUST be compatible with how Phase 2 calls them.





Files to Create or Modify



FULL REWRITE



| File | Purpose |

|------|---------|

| backend/storage/local.py | Local filesystem storage backend |

| backend/storage/s3.py | AWS S3 storage backend |

| backend/api/files.py | All file management API routes |

| backend/utils/path\_utils.py | Path sanitization and security utilities |



NEW FILES



| File | Purpose |

|------|---------|

| backend/tests/test\_file\_routes.py | File management test suite |

| backend/tests/test\_storage\_local.py | Local storage unit tests |

| backend/tests/test\_storage\_s3.py | S3 storage unit tests (mocked) |



DO NOT MODIFY

• backend/storage/base.py (abstract interface is stable)

• backend/api/dependencies.py (get\_storage already wired)

• backend/api/main.py (file router already included)

• backend/api/routes.py (Phase 2 complete)

• backend/auth/\* (Phase 1 complete)

• backend/pipeline/\* (Phase 2 complete)

• backend/models.py (stable)

• backend/config.py (stable)





Storage Architecture



Storage Areas



The storage layer organizes files into three logical areas, each mapping to

a subdirectory (local) or key prefix (S3):





storage\_root/

├── inputs/              # Loan tape files uploaded for processing

│   ├── daily/           # Organized by upload path

│   │   ├── loans\_2026-02-20.csv

│   │   └── loans\_2026-02-21.csv

│   └── weekly/

│       └── batch\_tape.xlsx

│

├── outputs/             # Pipeline-generated output files

│   ├── {run\_id}/        # One directory per pipeline run

│   │   ├── purchase\_tape.csv

│   │   ├── projected\_tape.csv

│   │   ├── rejection\_report.csv

│   │   └── exception\_summary.csv

│   └── {run\_id\_2}/

│       └── ...

│

└── output\_share/        # Shared output files (reports, exports)

&nbsp;   └── exports/

&nbsp;       └── exceptions\_2026-02-20.csv



Security Requirements



ALL storage operations MUST enforce:

1\. Path traversal prevention: No .. in paths, no absolute paths, no symlink following

2\. Area isolation: Operations in "inputs" cannot access "outputs" or vice versa

3\. File type validation on upload: Only allow: .csv, .xlsx, .xls, .json, .txt, .pdf, .zip

4\. File size limit on upload: Maximum 100MB per file

5\. Safe filename handling: Sanitize filenames to remove special characters





backend/utils/path\_utils.py — Complete Implementation



python

"""

Path sanitization and security utilities.

All file operations MUST use these functions to prevent path traversal attacks.

"""

import os

import re

import unicodedata

from pathlib import PurePosixPath

from typing import Optional



Allowed file extensions for upload

ALLOWED\_EXTENSIONS = {

&nbsp;   ".csv", ".xlsx", ".xls", ".json", ".txt", ".pdf", ".zip",

}



Maximum file size: 100 MB

MAX\_FILE\_SIZE\_BYTES = 100  1024  1024



Valid storage areas

VALID\_AREAS = {"inputs", "outputs", "output\_share"}



Characters to strip from filenames

UNSAFE\_FILENAME\_CHARS = re.compile(r'\[<>:"/\\\\|?\*\\x00-\\x1f]')



def validate\_area(area: str) -> str:

&nbsp;   """Validate and return the storage area."""

&nbsp;   if area not in VALID\_AREAS:

&nbsp;       raise ValueError(f"Invalid storage area: '{area}'. Must be one of: {VALID\_AREAS}")

&nbsp;   return area



def sanitize\_filename(filename: str) -> str:

&nbsp;   """

&nbsp;   Sanitize a filename for safe storage.

• Normalize unicode characters

• Remove unsafe characters

• Collapse whitespace to underscores

• Strip leading/trailing dots and spaces

• Ensure non-empty

&nbsp;   """

&nbsp;   if not filename:

&nbsp;       raise ValueError("Filename cannot be empty")



&nbsp;   # Normalize unicode

&nbsp;   filename = unicodedata.normalize("NFKD", filename)



&nbsp;   # Remove unsafe characters

&nbsp;   filename = UNSAFE\_FILENAME\_CHARS.sub("", filename)



&nbsp;   # Replace whitespace with underscores

&nbsp;   filename = re.sub(r'\\s+', '\_', filename)



&nbsp;   # Strip leading/trailing dots and spaces

&nbsp;   filename = filename.strip(". ")



&nbsp;   # Ensure non-empty after sanitization

&nbsp;   if not filename:

&nbsp;       raise ValueError("Filename is empty after sanitization")



&nbsp;   return filename



def validate\_file\_extension(filename: str) -> str:

&nbsp;   """Validate that the file has an allowed extension."""

&nbsp;   ext = os.path.splitext(filename)\[1].lower()

&nbsp;   if ext not in ALLOWED\_EXTENSIONS:

&nbsp;       raise ValueError(

&nbsp;           f"File type '{ext}' not allowed. "

&nbsp;           f"Permitted types: {', '.join(sorted(ALLOWED\_EXTENSIONS))}"

&nbsp;       )

&nbsp;   return ext



def safe\_join(base\_path: str, \*parts: str) -> str:

&nbsp;   """

&nbsp;   Safely join path components, preventing directory traversal.

&nbsp;   All paths are treated as POSIX paths (forward slashes) for

&nbsp;   compatibility between local filesystem and S3 keys.



&nbsp;   Raises ValueError if the resulting path escapes the base directory.

&nbsp;   """

&nbsp;   # Normalize parts: strip leading slashes, reject absolute paths

&nbsp;   cleaned\_parts = \[]

&nbsp;   for part in parts:

&nbsp;       if not part:

&nbsp;           continue

&nbsp;       # Convert backslashes to forward slashes

&nbsp;       part = part.replace("\\\\", "/")

&nbsp;       # Strip leading slash

&nbsp;       part = part.lstrip("/")

&nbsp;       # Reject path components with ..

&nbsp;       segments = part.split("/")

&nbsp;       for segment in segments:

&nbsp;           if segment == "..":

&nbsp;               raise ValueError(f"Path traversal detected: '{part}'")

&nbsp;           if segment.startswith("~"):

&nbsp;               raise ValueError(f"Home directory reference not allowed: '{part}'")

&nbsp;       cleaned\_parts.extend(segments)



&nbsp;   # Build final path

&nbsp;   result = PurePosixPath(base\_path)

&nbsp;   for part in cleaned\_parts:

&nbsp;       if part and part != ".":

&nbsp;           result = result / part



&nbsp;   # Verify the result is still under base\_path

&nbsp;   result\_str = str(result)

&nbsp;   base\_str = str(PurePosixPath(base\_path))

&nbsp;   if not result\_str.startswith(base\_str):

&nbsp;       raise ValueError(f"Path escapes base directory: '{result\_str}'")



&nbsp;   return result\_str



def validate\_file\_size(size: int) -> None:

&nbsp;   """Validate file size is within limits."""

&nbsp;   if size > MAX\_FILE\_SIZE\_BYTES:

&nbsp;       max\_mb = MAX\_FILE\_SIZE\_BYTES / (1024 \* 1024)

&nbsp;       actual\_mb = size / (1024 \* 1024)

&nbsp;       raise ValueError(

&nbsp;           f"File size ({actual\_mb:.1f}MB) exceeds maximum ({max\_mb:.0f}MB)"

&nbsp;       )



def get\_content\_type(filename: str) -> str:

&nbsp;   """Return the MIME content type for a filename."""

&nbsp;   ext = os.path.splitext(filename)\[1].lower()

&nbsp;   content\_types = {

&nbsp;       ".csv": "text/csv",

&nbsp;       ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

&nbsp;       ".xls": "application/vnd.ms-excel",

&nbsp;       ".json": "application/json",

&nbsp;       ".txt": "text/plain",

&nbsp;       ".pdf": "application/pdf",

&nbsp;       ".zip": "application/zip",

&nbsp;   }

&nbsp;   return content\_types.get(ext, "application/octet-stream")



def normalize\_storage\_path(path: str) -> str:

&nbsp;   """

&nbsp;   Normalize a storage path:

• Convert backslashes to forward slashes

• Remove leading/trailing slashes

• Collapse multiple slashes

• Remove . components

&nbsp;   """

&nbsp;   path = path.replace("\\\\", "/")

&nbsp;   path = re.sub(r'/+', '/', path)

&nbsp;   path = path.strip("/")

&nbsp;   parts = \[p for p in path.split("/") if p and p != "."]

&nbsp;   return "/".join(parts)





backend/storage/local.py — Local Filesystem Backend



python

"""

Local filesystem storage backend.

Stores files under a configurable base directory with area subdirectories.

Used in development and testing environments.

"""

import os

import logging

import shutil

import aiofiles

import aiofiles.os

from pathlib import Path

from datetime import datetime, timezone

from typing import AsyncGenerator

from io import BytesIO



from fastapi import UploadFile, HTTPException, status

from fastapi.responses import StreamingResponse



from backend.storage.base import StorageBackend

from backend.utils.path\_utils import (

&nbsp;   safe\_join,

&nbsp;   sanitize\_filename,

&nbsp;   validate\_area,

&nbsp;   validate\_file\_extension,

&nbsp;   validate\_file\_size,

&nbsp;   get\_content\_type,

&nbsp;   normalize\_storage\_path,

&nbsp;   VALID\_AREAS,

)



logger = logging.getLogger(\_\_name\_\_)



class LocalStorage(StorageBackend):

&nbsp;   """

&nbsp;   Local filesystem storage implementation.



&nbsp;   Directory structure:

&nbsp;       {base\_path}/

&nbsp;       ├── inputs/

&nbsp;       ├── outputs/

&nbsp;       └── output\_share/

&nbsp;   """



&nbsp;   def \_\_init\_\_(self, base\_path: str):

&nbsp;       self.base\_path = Path(base\_path).resolve()

&nbsp;       self.\_ensure\_directories()



&nbsp;   def \_ensure\_directories(self):

&nbsp;       """Create area directories if they don't exist."""

&nbsp;       for area in VALID\_AREAS:

&nbsp;           area\_path = self.base\_path / area

&nbsp;           area\_path.mkdir(parents=True, exist\_ok=True)



&nbsp;   def \_resolve\_path(self, path: str, area: str) -> Path:

&nbsp;       """

&nbsp;       Resolve a relative path within a storage area to an absolute path.

&nbsp;       Raises ValueError on path traversal attempts.

&nbsp;       """

&nbsp;       validate\_area(area)

&nbsp;       area\_base = str(self.base\_path / area)

&nbsp;       safe\_path = safe\_join(area\_base, normalize\_storage\_path(path))

&nbsp;       resolved = Path(safe\_path).resolve()



&nbsp;       # Double-check the resolved path is under the area directory

&nbsp;       area\_resolved = (self.base\_path / area).resolve()

&nbsp;       if not str(resolved).startswith(str(area\_resolved)):

&nbsp;           raise ValueError(f"Path traversal detected: {path}")



&nbsp;       return resolved



&nbsp;   async def list\_files(

&nbsp;       self, path: str, recursive: bool = False, area: str = "inputs"

&nbsp;   ) -> list\[dict]:

&nbsp;       """List files and directories at the given path."""

&nbsp;       try:

&nbsp;           target = self.\_resolve\_path(path, area)

&nbsp;       except ValueError as e:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=str(e),

&nbsp;           )



&nbsp;       if not target.exists():

&nbsp;           return \[]



&nbsp;       if not target.is\_dir():

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=f"Path is not a directory: {path}",

&nbsp;           )



&nbsp;       results = \[]

&nbsp;       area\_base = (self.base\_path / area).resolve()



&nbsp;       if recursive:

&nbsp;           for root, dirs, files in os.walk(target):

&nbsp;               # Skip hidden directories

&nbsp;               dirs\[:] = \[d for d in dirs if not d.startswith(".")]

&nbsp;               for name in sorted(files):

&nbsp;                   if name.startswith("."):

&nbsp;                       continue

&nbsp;                   file\_path = Path(root) / name

&nbsp;                   stat = file\_path.stat()

&nbsp;                   rel\_path = file\_path.relative\_to(area\_base)

&nbsp;                   results.append({

&nbsp;                       "name": name,

&nbsp;                       "path": str(rel\_path).replace("\\\\", "/"),

&nbsp;                       "type": "file",

&nbsp;                       "size": stat.st\_size,

&nbsp;                       "last\_modified": datetime.fromtimestamp(

&nbsp;                           stat.st\_mtime, tz=timezone.utc

&nbsp;                       ).isoformat(),

&nbsp;                   })

&nbsp;               for name in sorted(dirs):

&nbsp;                   dir\_path = Path(root) / name

&nbsp;                   rel\_path = dir\_path.relative\_to(area\_base)

&nbsp;                   results.append({

&nbsp;                       "name": name,

&nbsp;                       "path": str(rel\_path).replace("\\\\", "/"),

&nbsp;                       "type": "directory",

&nbsp;                       "size": 0,

&nbsp;                       "last\_modified": datetime.fromtimestamp(

&nbsp;                           dir\_path.stat().st\_mtime, tz=timezone.utc

&nbsp;                       ).isoformat(),

&nbsp;                   })

&nbsp;       else:

&nbsp;           for item in sorted(target.iterdir()):

&nbsp;               if item.name.startswith("."):

&nbsp;                   continue

&nbsp;               stat = item.stat()

&nbsp;               rel\_path = item.relative\_to(area\_base)

&nbsp;               results.append({

&nbsp;                   "name": item.name,

&nbsp;                   "path": str(rel\_path).replace("\\\\", "/"),

&nbsp;                   "type": "directory" if item.is\_dir() else "file",

&nbsp;                   "size": stat.st\_size if item.is\_file() else 0,

&nbsp;                   "last\_modified": datetime.fromtimestamp(

&nbsp;                       stat.st\_mtime, tz=timezone.utc

&nbsp;                   ).isoformat(),

&nbsp;               })



&nbsp;       return results



&nbsp;   async def upload\_file(

&nbsp;       self, file: UploadFile, destination: str, area: str = "inputs"

&nbsp;   ) -> dict:

&nbsp;       """Upload a file to the specified destination."""

&nbsp;       # Sanitize and validate filename

&nbsp;       filename = sanitize\_filename(file.filename or "unnamed")

&nbsp;       validate\_file\_extension(filename)



&nbsp;       # Determine destination path

&nbsp;       dest\_normalized = normalize\_storage\_path(destination)



&nbsp;       # If destination ends with a filename (has extension), use it as-is

&nbsp;       # Otherwise treat as directory and append the filename

&nbsp;       if os.path.splitext(dest\_normalized)\[1]:

&nbsp;           target\_rel = dest\_normalized

&nbsp;       else:

&nbsp;           target\_rel = f"{dest\_normalized}/{filename}" if dest\_normalized else filename



&nbsp;       try:

&nbsp;           target\_path = self.\_resolve\_path(target\_rel, area)

&nbsp;       except ValueError as e:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=str(e),

&nbsp;           )



&nbsp;       # Read file content and validate size

&nbsp;       content = await file.read()

&nbsp;       validate\_file\_size(len(content))



&nbsp;       # Ensure parent directory exists

&nbsp;       target\_path.parent.mkdir(parents=True, exist\_ok=True)



&nbsp;       # Write file

&nbsp;       async with aiofiles.open(target\_path, "wb") as f:

&nbsp;           await f.write(content)



&nbsp;       area\_base = (self.base\_path / area).resolve()

&nbsp;       rel\_path = target\_path.relative\_to(area\_base)



&nbsp;       logger.info("Uploaded %s to %s/%s (%d bytes)",

&nbsp;                    filename, area, rel\_path, len(content))



&nbsp;       return {

&nbsp;           "filename": filename,

&nbsp;           "path": str(rel\_path).replace("\\\\", "/"),

&nbsp;           "area": area,

&nbsp;           "size": len(content),

&nbsp;           "status": "uploaded",

&nbsp;       }



&nbsp;   async def download\_file(

&nbsp;       self, path: str, area: str = "inputs"

&nbsp;   ) -> StreamingResponse:

&nbsp;       """Download a file as a streaming response."""

&nbsp;       try:

&nbsp;           file\_path = self.\_resolve\_path(path, area)

&nbsp;       except ValueError as e:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=str(e),

&nbsp;           )



&nbsp;       if not file\_path.exists():

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;               detail=f"File not found: {path}",

&nbsp;           )



&nbsp;       if not file\_path.is\_file():

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=f"Path is not a file: {path}",

&nbsp;           )



&nbsp;       filename = file\_path.name

&nbsp;       content\_type = get\_content\_type(filename)



&nbsp;       async def file\_stream() -> AsyncGenerator\[bytes, None]:

&nbsp;           async with aiofiles.open(file\_path, "rb") as f:

&nbsp;               while chunk := await f.read(8192):

&nbsp;                   yield chunk



&nbsp;       return StreamingResponse(

&nbsp;           file\_stream(),

&nbsp;           media\_type=content\_type,

&nbsp;           headers={

&nbsp;               "Content-Disposition": f'attachment; filename="{filename}"',

&nbsp;               "Content-Length": str(file\_path.stat().st\_size),

&nbsp;           },

&nbsp;       )



&nbsp;   async def delete\_file(

&nbsp;       self, path: str, area: str = "inputs"

&nbsp;   ) -> dict:

&nbsp;       """Delete a file."""

&nbsp;       try:

&nbsp;           file\_path = self.\_resolve\_path(path, area)

&nbsp;       except ValueError as e:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=str(e),

&nbsp;           )



&nbsp;       if not file\_path.exists():

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;               detail=f"File not found: {path}",

&nbsp;           )



&nbsp;       if file\_path.is\_dir():

&nbsp;           # Only allow deleting empty directories

&nbsp;           if any(file\_path.iterdir()):

&nbsp;               raise HTTPException(

&nbsp;                   status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;                   detail="Directory is not empty. Delete contents first.",

&nbsp;               )

&nbsp;           file\_path.rmdir()

&nbsp;           file\_type = "directory"

&nbsp;       else:

&nbsp;           file\_path.unlink()

&nbsp;           file\_type = "file"



&nbsp;       logger.info("Deleted %s: %s/%s", file\_type, area, path)



&nbsp;       return {

&nbsp;           "path": path,

&nbsp;           "area": area,

&nbsp;           "type": file\_type,

&nbsp;           "status": "deleted",

&nbsp;       }



&nbsp;   async def create\_directory(

&nbsp;       self, path: str, area: str = "inputs"

&nbsp;   ) -> dict:

&nbsp;       """Create a directory."""

&nbsp;       try:

&nbsp;           dir\_path = self.\_resolve\_path(path, area)

&nbsp;       except ValueError as e:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=str(e),

&nbsp;           )



&nbsp;       if dir\_path.exists():

&nbsp;           if dir\_path.is\_dir():

&nbsp;               return {"path": path, "area": area, "status": "exists"}

&nbsp;           else:

&nbsp;               raise HTTPException(

&nbsp;                   status\_code=status.HTTP\_409\_CONFLICT,

&nbsp;                   detail=f"A file already exists at this path: {path}",

&nbsp;               )



&nbsp;       dir\_path.mkdir(parents=True, exist\_ok=True)



&nbsp;       logger.info("Created directory: %s/%s", area, path)



&nbsp;       return {"path": path, "area": area, "status": "created"}



&nbsp;   async def get\_presigned\_url(

&nbsp;       self, path: str, expires\_in: int = 3600, area: str = "inputs"

&nbsp;   ) -> str:

&nbsp;       """

&nbsp;       For local storage, return the local file path.

&nbsp;       (Presigned URLs are an S3 concept; locally we return the path.)

&nbsp;       """

&nbsp;       try:

&nbsp;           file\_path = self.\_resolve\_path(path, area)

&nbsp;       except ValueError as e:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail=str(e),

&nbsp;           )



&nbsp;       if not file\_path.exists():

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;               detail=f"File not found: {path}",

&nbsp;           )



&nbsp;       return str(file\_path)





backend/storage/s3.py — S3 Storage Backend



python

"""

AWS S3 storage backend.

Stores files in an S3 bucket with area-based key prefixes.

Used in test and production environments.

"""

import logging

from io import BytesIO

from datetime import datetime, timezone



import boto3

from botocore.exceptions import ClientError, NoCredentialsError



from fastapi import UploadFile, HTTPException, status

from fastapi.responses import StreamingResponse



from backend.storage.base import StorageBackend

from backend.utils.path\_utils import (

&nbsp;   safe\_join,

&nbsp;   sanitize\_filename,

&nbsp;   validate\_area,

&nbsp;   validate\_file\_extension,

&nbsp;   validate\_file\_size,

&nbsp;   get\_content\_type,

&nbsp;   normalize\_storage\_path,

)



logger = logging.getLogger(\_\_name\_\_)



class S3Storage(StorageBackend):

&nbsp;   """

&nbsp;   AWS S3 storage implementation.



&nbsp;   Key structure:

&nbsp;       {bucket}/

&nbsp;       ├── inputs/...

&nbsp;       ├── outputs/...

&nbsp;       └── output\_share/...

&nbsp;   """



&nbsp;   def \_\_init\_\_(

&nbsp;       self,

&nbsp;       bucket\_name: str,

&nbsp;       region: str = "us-east-1",

&nbsp;       aws\_access\_key\_id: str = "",

&nbsp;       aws\_secret\_access\_key: str = "",

&nbsp;   ):

&nbsp;       self.bucket\_name = bucket\_name

&nbsp;       self.region = region



&nbsp;       # Build boto3 client

&nbsp;       client\_kwargs = {"region\_name": region}

&nbsp;       if aws\_access\_key\_id and aws\_secret\_access\_key:

&nbsp;           client\_kwargs\["aws\_access\_key\_id"] = aws\_access\_key\_id

&nbsp;           client\_kwargs\["aws\_secret\_access\_key"] = aws\_secret\_access\_key



&nbsp;       self.s3\_client = boto3.client("s3", client\_kwargs)



&nbsp;   def \_build\_key(self, path: str, area: str) -> str:

&nbsp;       """Build an S3 key from area and path."""

&nbsp;       validate\_area(area)

&nbsp;       normalized = normalize\_storage\_path(path)

&nbsp;       if normalized:

&nbsp;           key = safe\_join(area, normalized)

&nbsp;       else:

&nbsp;           key = area

&nbsp;       # safe\_join returns posix path; ensure no leading slash

&nbsp;       return key.lstrip("/")



&nbsp;   async def list\_files(

&nbsp;       self, path: str, recursive: bool = False, area: str = "inputs"

&nbsp;   ) -> list\[dict]:

&nbsp;       """List objects in the S3 bucket under the given prefix."""

&nbsp;       prefix = self.\_build\_key(path, area)

&nbsp;       if prefix and not prefix.endswith("/"):

&nbsp;           prefix += "/"



&nbsp;       try:

&nbsp;           results = \[]

&nbsp;           paginator = self.s3\_client.get\_paginator("list\_objects\_v2")



&nbsp;           page\_kwargs = {

&nbsp;               "Bucket": self.bucket\_name,

&nbsp;               "Prefix": prefix,

&nbsp;           }

&nbsp;           if not recursive:

&nbsp;               page\_kwargs\["Delimiter"] = "/"



&nbsp;           for page in paginator.paginate(page\_kwargs):

&nbsp;               # Files

&nbsp;               for obj in page.get("Contents", \[]):

&nbsp;                   key = obj\["Key"]

&nbsp;                   # Skip the prefix itself

&nbsp;                   if key == prefix:

&nbsp;                       continue

&nbsp;                   # Get relative path from area base

&nbsp;                   rel\_key = key\[len(area) + 1:]  # remove "area/" prefix

&nbsp;                   name = key.rsplit("/", 1)\[-1]

&nbsp;                   if not name:

&nbsp;                       continue

&nbsp;                   results.append({

&nbsp;                       "name": name,

&nbsp;                       "path": rel\_key,

&nbsp;                       "type": "file",

&nbsp;                       "size": obj\["Size"],

&nbsp;                       "last\_modified": obj\["LastModified"].isoformat(),

&nbsp;                   })



&nbsp;               # Directories (common prefixes)

&nbsp;               for prefix\_obj in page.get("CommonPrefixes", \[]):

&nbsp;                   dir\_prefix = prefix\_obj\["Prefix"]

&nbsp;                   rel\_key = dir\_prefix\[len(area) + 1:].rstrip("/")

&nbsp;                   name = rel\_key.rsplit("/", 1)\[-1]

&nbsp;                   if not name:

&nbsp;                       continue

&nbsp;                   results.append({

&nbsp;                       "name": name,

&nbsp;                       "path": rel\_key,

&nbsp;                       "type": "directory",

&nbsp;                       "size": 0,

&nbsp;                       "last\_modified": datetime.now(timezone.utc).isoformat(),

&nbsp;                   })



&nbsp;           return results



&nbsp;       except ClientError as e:

&nbsp;           error\_code = e.response\["Error"]\["Code"]

&nbsp;           logger.error("S3 list error: %s", e)

&nbsp;           if error\_code == "NoSuchBucket":

&nbsp;               raise HTTPException(

&nbsp;                   status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;                   detail="Storage bucket not configured",

&nbsp;               )

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail=f"Storage error: {error\_code}",

&nbsp;           )

&nbsp;       except NoCredentialsError:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail="Storage credentials not configured",

&nbsp;           )



&nbsp;   async def upload\_file(

&nbsp;       self, file: UploadFile, destination: str, area: str = "inputs"

&nbsp;   ) -> dict:

&nbsp;       """Upload a file to S3."""

&nbsp;       filename = sanitize\_filename(file.filename or "unnamed")

&nbsp;       validate\_file\_extension(filename)



&nbsp;       dest\_normalized = normalize\_storage\_path(destination)

&nbsp;       import os

&nbsp;       if os.path.splitext(dest\_normalized)\[1]:

&nbsp;           key = self.\_build\_key(dest\_normalized, area)

&nbsp;       else:

&nbsp;           rel\_path = f"{dest\_normalized}/{filename}" if dest\_normalized else filename

&nbsp;           key = self.\_build\_key(rel\_path, area)



&nbsp;       # Read and validate

&nbsp;       content = await file.read()

&nbsp;       validate\_file\_size(len(content))



&nbsp;       content\_type = get\_content\_type(filename)



&nbsp;       try:

&nbsp;           self.s3\_client.put\_object(

&nbsp;               Bucket=self.bucket\_name,

&nbsp;               Key=key,

&nbsp;               Body=content,

&nbsp;               ContentType=content\_type,

&nbsp;           )

&nbsp;       except ClientError as e:

&nbsp;           logger.error("S3 upload error: %s", e)

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail=f"Upload failed: {e.response\['Error']\['Code']}",

&nbsp;           )



&nbsp;       rel\_path = key\[len(area) + 1:]  # remove area prefix



&nbsp;       logger.info("Uploaded to s3://%s/%s (%d bytes)", self.bucket\_name, key, len(content))



&nbsp;       return {

&nbsp;           "filename": filename,

&nbsp;           "path": rel\_path,

&nbsp;           "area": area,

&nbsp;           "size": len(content),

&nbsp;           "status": "uploaded",

&nbsp;       }



&nbsp;   async def download\_file(

&nbsp;       self, path: str, area: str = "inputs"

&nbsp;   ) -> StreamingResponse:

&nbsp;       """Download a file from S3 as a streaming response."""

&nbsp;       key = self.\_build\_key(path, area)



&nbsp;       try:

&nbsp;           response = self.s3\_client.get\_object(

&nbsp;               Bucket=self.bucket\_name,

&nbsp;               Key=key,

&nbsp;           )

&nbsp;       except ClientError as e:

&nbsp;           error\_code = e.response\["Error"]\["Code"]

&nbsp;           if error\_code in ("NoSuchKey", "404"):

&nbsp;               raise HTTPException(

&nbsp;                   status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;                   detail=f"File not found: {path}",

&nbsp;               )

&nbsp;           logger.error("S3 download error: %s", e)

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail=f"Download failed: {error\_code}",

&nbsp;           )



&nbsp;       filename = path.rsplit("/", 1)\[-1]

&nbsp;       content\_type = get\_content\_type(filename)

&nbsp;       content\_length = response.get("ContentLength", 0)



&nbsp;       def stream\_body():

&nbsp;           body = response\["Body"]

&nbsp;           while chunk := body.read(8192):

&nbsp;               yield chunk



&nbsp;       return StreamingResponse(

&nbsp;           stream\_body(),

&nbsp;           media\_type=content\_type,

&nbsp;           headers={

&nbsp;               "Content-Disposition": f'attachment; filename="{filename}"',

&nbsp;               "Content-Length": str(content\_length),

&nbsp;           },

&nbsp;       )



&nbsp;   async def delete\_file(

&nbsp;       self, path: str, area: str = "inputs"

&nbsp;   ) -> dict:

&nbsp;       """Delete a file from S3."""

&nbsp;       key = self.\_build\_key(path, area)



&nbsp;       try:

&nbsp;           # Check existence first

&nbsp;           self.s3\_client.head\_object(Bucket=self.bucket\_name, Key=key)

&nbsp;       except ClientError as e:

&nbsp;           if e.response\["Error"]\["Code"] in ("404", "NoSuchKey"):

&nbsp;               raise HTTPException(

&nbsp;                   status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;                   detail=f"File not found: {path}",

&nbsp;               )

&nbsp;           raise



&nbsp;       try:

&nbsp;           self.s3\_client.delete\_object(Bucket=self.bucket\_name, Key=key)

&nbsp;       except ClientError as e:

&nbsp;           logger.error("S3 delete error: %s", e)

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail=f"Delete failed: {e.response\['Error']\['Code']}",

&nbsp;           )



&nbsp;       logger.info("Deleted s3://%s/%s", self.bucket\_name, key)



&nbsp;       return {

&nbsp;           "path": path,

&nbsp;           "area": area,

&nbsp;           "type": "file",

&nbsp;           "status": "deleted",

&nbsp;       }



&nbsp;   async def create\_directory(

&nbsp;       self, path: str, area: str = "inputs"

&nbsp;   ) -> dict:

&nbsp;       """

&nbsp;       Create a 'directory' in S3 (a zero-byte object with trailing slash).

&nbsp;       S3 doesn't have real directories, but this creates a visible prefix.

&nbsp;       """

&nbsp;       dir\_path = normalize\_storage\_path(path)

&nbsp;       if not dir\_path.endswith("/"):

&nbsp;           dir\_path += "/"

&nbsp;       key = self.\_build\_key(dir\_path, area)



&nbsp;       try:

&nbsp;           self.s3\_client.put\_object(

&nbsp;               Bucket=self.bucket\_name,

&nbsp;               Key=key,

&nbsp;               Body=b"",

&nbsp;           )

&nbsp;       except ClientError as e:

&nbsp;           logger.error("S3 mkdir error: %s", e)

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail=f"Directory creation failed: {e.response\['Error']\['Code']}",

&nbsp;           )



&nbsp;       logger.info("Created directory s3://%s/%s", self.bucket\_name, key)



&nbsp;       return {"path": path, "area": area, "status": "created"}



&nbsp;   async def get\_presigned\_url(

&nbsp;       self, path: str, expires\_in: int = 3600, area: str = "inputs"

&nbsp;   ) -> str:

&nbsp;       """Generate a presigned URL for temporary file access."""

&nbsp;       key = self.\_build\_key(path, area)



&nbsp;       try:

&nbsp;           # Verify the object exists

&nbsp;           self.s3\_client.head\_object(Bucket=self.bucket\_name, Key=key)

&nbsp;       except ClientError as e:

&nbsp;           if e.response\["Error"]\["Code"] in ("404", "NoSuchKey"):

&nbsp;               raise HTTPException(

&nbsp;                   status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;                   detail=f"File not found: {path}",

&nbsp;               )

&nbsp;           raise



&nbsp;       try:

&nbsp;           url = self.s3\_client.generate\_presigned\_url(

&nbsp;               "get\_object",

&nbsp;               Params={"Bucket": self.bucket\_name, "Key": key},

&nbsp;               ExpiresIn=expires\_in,

&nbsp;           )

&nbsp;       except ClientError as e:

&nbsp;           logger.error("S3 presigned URL error: %s", e)

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;               detail="Failed to generate file URL",

&nbsp;           )



&nbsp;       return url





backend/api/files.py — Complete Route Implementation



Replace the entire file with the full implementation:



python

"""

File management API routes.

Handles upload, download, listing, deletion, and directory operations.

All operations delegate to the configured StorageBackend (local or S3).

"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status

from fastapi.responses import StreamingResponse



from backend.auth.security import get\_current\_user

from backend.api.dependencies import get\_storage

from backend.storage.base import StorageBackend

from backend.models import User

from backend.utils.path\_utils import (

&nbsp;   validate\_area,

&nbsp;   normalize\_storage\_path,

&nbsp;   VALID\_AREAS,

)



logger = logging.getLogger(\_\_name\_\_)

router = APIRouter()



@router.get("/list")

async def list\_files(

&nbsp;   path: str = Query("", description="Directory path to list"),

&nbsp;   recursive: bool = Query(False, description="List files recursively"),

&nbsp;   area: str = Query("inputs", description="Storage area: inputs | outputs | output\_share"),

&nbsp;   storage\_type: str | None = Query(None, description="Override storage type (local/s3)"),

&nbsp;   current\_user: User = Depends(get\_current\_user),

&nbsp;   storage: StorageBackend = Depends(get\_storage),

):

&nbsp;   """List files in a directory."""

&nbsp;   try:

&nbsp;       validate\_area(area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   normalized\_path = normalize\_storage\_path(path)

&nbsp;   files = await storage.list\_files(normalized\_path, recursive=recursive, area=area)



&nbsp;   return {

&nbsp;       "path": normalized\_path,

&nbsp;       "area": area,

&nbsp;       "recursive": recursive,

&nbsp;       "count": len(files),

&nbsp;       "files": files,

&nbsp;   }



@router.post("/upload")

async def upload\_file(

&nbsp;   file: UploadFile = File(..., description="File to upload"),

&nbsp;   path: str = Query("", description="Destination path (directory or full file path)"),

&nbsp;   area: str = Query("inputs", description="Storage area: inputs | outputs | output\_share"),

&nbsp;   storage\_type: str | None = Query(None, description="Override storage type (local/s3)"),

&nbsp;   current\_user: User = Depends(get\_current\_user),

&nbsp;   storage: StorageBackend = Depends(get\_storage),

):

&nbsp;   """

&nbsp;   Upload a file.

&nbsp;   When using S3, uploads always go to the inputs area so the pipeline can read them.

&nbsp;   """

&nbsp;   try:

&nbsp;       validate\_area(area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   normalized\_path = normalize\_storage\_path(path)



&nbsp;   try:

&nbsp;       result = await storage.upload\_file(file, normalized\_path, area=area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   logger.info("User '%s' uploaded file to %s/%s",

&nbsp;               current\_user.username, area, result.get("path", ""))



&nbsp;   return result



@router.get("/download/{file\_path:path}")

async def download\_file(

&nbsp;   file\_path: str,

&nbsp;   area: str = Query("inputs", description="Storage area: inputs | outputs | output\_share"),

&nbsp;   storage\_type: str | None = Query(None, description="Override storage type (local/s3)"),

&nbsp;   current\_user: User = Depends(get\_current\_user),

&nbsp;   storage: StorageBackend = Depends(get\_storage),

):

&nbsp;   """Download a file."""

&nbsp;   try:

&nbsp;       validate\_area(area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   normalized\_path = normalize\_storage\_path(file\_path)



&nbsp;   if not normalized\_path:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;           detail="File path is required",

&nbsp;       )



&nbsp;   return await storage.download\_file(normalized\_path, area=area)



@router.get("/url/{file\_path:path}")

async def get\_file\_url(

&nbsp;   file\_path: str,

&nbsp;   expires\_in: int = Query(3600, description="URL expiration time in seconds"),

&nbsp;   area: str = Query("inputs", description="Storage area: inputs | outputs | output\_share"),

&nbsp;   storage\_type: str | None = Query(None, description="Override storage type (local/s3)"),

&nbsp;   current\_user: User = Depends(get\_current\_user),

&nbsp;   storage: StorageBackend = Depends(get\_storage),

):

&nbsp;   """Get a presigned URL for file access (S3) or file path (local)."""

&nbsp;   try:

&nbsp;       validate\_area(area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   normalized\_path = normalize\_storage\_path(file\_path)



&nbsp;   if not normalized\_path:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;           detail="File path is required",

&nbsp;       )



&nbsp;   url = await storage.get\_presigned\_url(normalized\_path, expires\_in=expires\_in, area=area)



&nbsp;   return {

&nbsp;       "path": normalized\_path,

&nbsp;       "area": area,

&nbsp;       "url": url,

&nbsp;       "expires\_in": expires\_in,

&nbsp;   }



@router.delete("/{file\_path:path}")

async def delete\_file(

&nbsp;   file\_path: str,

&nbsp;   area: str = Query("inputs", description="Storage area: inputs | outputs | output\_share"),

&nbsp;   storage\_type: str | None = Query(None, description="Override storage type (local/s3)"),

&nbsp;   current\_user: User = Depends(get\_current\_user),

&nbsp;   storage: StorageBackend = Depends(get\_storage),

):

&nbsp;   """Delete a file."""

&nbsp;   try:

&nbsp;       validate\_area(area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   normalized\_path = normalize\_storage\_path(file\_path)



&nbsp;   if not normalized\_path:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;           detail="File path is required",

&nbsp;       )



&nbsp;   result = await storage.delete\_file(normalized\_path, area=area)



&nbsp;   logger.info("User '%s' deleted %s/%s",

&nbsp;               current\_user.username, area, normalized\_path)



&nbsp;   return result



@router.post("/mkdir")

async def create\_directory(

&nbsp;   path: str = Query(..., description="Directory path to create"),

&nbsp;   area: str = Query("inputs", description="Storage area: inputs | outputs | output\_share"),

&nbsp;   storage\_type: str | None = Query(None, description="Override storage type (local/s3)"),

&nbsp;   current\_user: User = Depends(get\_current\_user),

&nbsp;   storage: StorageBackend = Depends(get\_storage),

):

&nbsp;   """Create a directory."""

&nbsp;   try:

&nbsp;       validate\_area(area)

&nbsp;   except ValueError as e:

&nbsp;       raise HTTPException(status\_code=status.HTTP\_400\_BAD\_REQUEST, detail=str(e))



&nbsp;   normalized\_path = normalize\_storage\_path(path)



&nbsp;   if not normalized\_path:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;           detail="Directory path is required",

&nbsp;       )



&nbsp;   result = await storage.create\_directory(normalized\_path, area=area)



&nbsp;   logger.info("User '%s' created directory %s/%s",

&nbsp;               current\_user.username, area, normalized\_path)



&nbsp;   return result





Test Suite: backend/tests/test\_file\_routes.py



python

"""

Comprehensive tests for file management endpoints.

Uses LocalStorage with a temporary directory.

"""

import pytest

import os

import tempfile

from pathlib import Path

from io import BytesIO

from httpx import AsyncClient



from backend.api.dependencies import get\_storage

from backend.storage.local import LocalStorage

from backend.api.main import app



def auth\_header(token: str) -> dict:

&nbsp;   return {"Authorization": f"Bearer {token}"}



@pytest.fixture

def temp\_storage(tmp\_path):

&nbsp;   """Create a temporary storage directory with test files."""

&nbsp;   storage = LocalStorage(base\_path=str(tmp\_path))



&nbsp;   # Create test files in inputs

&nbsp;   inputs\_dir = tmp\_path / "inputs"

&nbsp;   (inputs\_dir / "test\_loans.csv").write\_text("loan\_number,amount\\nLOAN-001,150000\\n")

&nbsp;   (inputs\_dir / "test\_tape.xlsx").write\_bytes(b"fake xlsx content")

&nbsp;   (inputs\_dir / "subdir").mkdir()

&nbsp;   (inputs\_dir / "subdir" / "nested.csv").write\_text("col1,col2\\na,b\\n")



&nbsp;   # Create test files in outputs

&nbsp;   outputs\_dir = tmp\_path / "outputs"

&nbsp;   run\_dir = outputs\_dir / "test-run-001"

&nbsp;   run\_dir.mkdir(parents=True)

&nbsp;   (run\_dir / "purchase\_tape.csv").write\_text("loan\_number,disposition\\nLOAN-001,to\_purchase\\n")

&nbsp;   (run\_dir / "rejection\_report.csv").write\_text("loan\_number,reason\\nLOAN-002,ltv\\n")



&nbsp;   return storage



@pytest.fixture

def override\_storage(temp\_storage):

&nbsp;   """Override the storage dependency with temp storage."""

&nbsp;   app.dependency\_overrides\[get\_storage] = lambda: temp\_storage

&nbsp;   yield temp\_storage

&nbsp;   app.dependency\_overrides.pop(get\_storage, None)



─── GET /api/files/list ─────────────────────────────────────────────────



class TestListFiles:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_inputs\_root(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert body\["area"] == "inputs"

&nbsp;       assert body\["count"] >= 2

&nbsp;       names = \[f\["name"] for f in body\["files"]]

&nbsp;       assert "test\_loans.csv" in names

&nbsp;       assert "subdir" in names



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_subdirectory(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"path": "subdir", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       names = \[f\["name"] for f in response.json()\["files"]]

&nbsp;       assert "nested.csv" in names



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_recursive(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"recursive": True, "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       paths = \[f\["path"] for f in response.json()\["files"]]

&nbsp;       assert any("nested.csv" in p for p in paths)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_outputs(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"path": "test-run-001", "area": "outputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       names = \[f\["name"] for f in response.json()\["files"]]

&nbsp;       assert "purchase\_tape.csv" in names



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_nonexistent\_path(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"path": "nonexistent", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert response.json()\["count"] == 0



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_invalid\_area(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"area": "invalid"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_unauthenticated(self, async\_client, override\_storage):

&nbsp;       response = await async\_client.get("/api/files/list")

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_path\_traversal\_blocked(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"path": "../../etc", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400



─── POST /api/files/upload ──────────────────────────────────────────────



class TestUploadFile:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_csv(self, async\_client, admin\_token, override\_storage):

&nbsp;       content = b"col1,col2\\nval1,val2\\n"

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           params={"area": "inputs"},

&nbsp;           files={"file": ("upload\_test.csv", BytesIO(content), "text/csv")},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert body\["status"] == "uploaded"

&nbsp;       assert body\["filename"] == "upload\_test.csv"

&nbsp;       assert body\["size"] == len(content)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_to\_subdirectory(self, async\_client, admin\_token, override\_storage):

&nbsp;       content = b"data"

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           params={"path": "daily", "area": "inputs"},

&nbsp;           files={"file": ("batch.csv", BytesIO(content), "text/csv")},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert "daily" in response.json()\["path"]



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_disallowed\_extension(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           params={"area": "inputs"},

&nbsp;           files={"file": ("malicious.exe", BytesIO(b"bad"), "application/octet-stream")},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_unauthenticated(self, async\_client, override\_storage):

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           files={"file": ("test.csv", BytesIO(b"data"), "text/csv")},

&nbsp;       )

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_path\_traversal\_blocked(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           params={"path": "../../etc", "area": "inputs"},

&nbsp;           files={"file": ("test.csv", BytesIO(b"data"), "text/csv")},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400



─── GET /api/files/download/{file\_path} ─────────────────────────────────



class TestDownloadFile:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_existing\_file(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/download/test\_loans.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert "text/csv" in response.headers.get("content-type", "")

&nbsp;       assert b"loan\_number" in response.content



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_nested\_file(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/download/subdir/nested.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_output\_file(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/download/test-run-001/purchase\_tape.csv",

&nbsp;           params={"area": "outputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert b"to\_purchase" in response.content



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_nonexistent(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/download/nonexistent.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_path\_traversal\_blocked(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/download/../../etc/passwd",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400



─── GET /api/files/url/{file\_path} ──────────────────────────────────────



class TestGetFileUrl:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_url\_existing\_file(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/url/test\_loans.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert "url" in body

&nbsp;       assert body\["area"] == "inputs"



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_url\_nonexistent(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/url/nonexistent.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_url\_custom\_expiration(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/files/url/test\_loans.csv",

&nbsp;           params={"area": "inputs", "expires\_in": 7200},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert response.json()\["expires\_in"] == 7200



─── DELETE /api/files/{file\_path} ───────────────────────────────────────



class TestDeleteFile:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_delete\_file(self, async\_client, admin\_token, override\_storage, temp\_storage):

&nbsp;       # First upload a file to delete

&nbsp;       content = b"temporary"

&nbsp;       await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           params={"area": "inputs"},

&nbsp;           files={"file": ("to\_delete.csv", BytesIO(content), "text/csv")},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )



&nbsp;       # Delete it

&nbsp;       response = await async\_client.delete(

&nbsp;           "/api/files/to\_delete.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert response.json()\["status"] == "deleted"



&nbsp;       # Verify it's gone

&nbsp;       download = await async\_client.get(

&nbsp;           "/api/files/download/to\_delete.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert download.status\_code == 404



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_delete\_nonexistent(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.delete(

&nbsp;           "/api/files/ghost.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_delete\_unauthenticated(self, async\_client, override\_storage):

&nbsp;       response = await async\_client.delete("/api/files/test.csv")

&nbsp;       assert response.status\_code == 401



─── POST /api/files/mkdir ───────────────────────────────────────────────



class TestCreateDirectory:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_create\_directory(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/mkdir",

&nbsp;           params={"path": "new\_folder", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert response.json()\["status"] in ("created", "exists")



&nbsp;       # Verify it appears in listing

&nbsp;       list\_response = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       names = \[f\["name"] for f in list\_response.json()\["files"]]

&nbsp;       assert "new\_folder" in names



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_create\_nested\_directory(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/mkdir",

&nbsp;           params={"path": "level1/level2/level3", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_create\_directory\_idempotent(self, async\_client, admin\_token, override\_storage):

&nbsp;       params = {"path": "idempotent\_dir", "area": "inputs"}

&nbsp;       r1 = await async\_client.post("/api/files/mkdir", params=params, headers=auth\_header(admin\_token))

&nbsp;       r2 = await async\_client.post("/api/files/mkdir", params=params, headers=auth\_header(admin\_token))

&nbsp;       assert r1.status\_code == 200

&nbsp;       assert r2.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_mkdir\_path\_traversal\_blocked(self, async\_client, admin\_token, override\_storage):

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/files/mkdir",

&nbsp;           params={"path": "../../escape", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400



─── Integration: Upload → List → Download → Delete ─────────────────────



class TestFileIntegration:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_full\_file\_lifecycle(self, async\_client, admin\_token, override\_storage):

&nbsp;       """Upload → List → Download → Delete lifecycle."""

&nbsp;       csv\_content = b"seller\_loan\_number,loan\_amount\\nLOAN-999,500000\\n"



&nbsp;       # 1. Upload

&nbsp;       upload\_resp = await async\_client.post(

&nbsp;           "/api/files/upload",

&nbsp;           params={"path": "lifecycle\_test", "area": "inputs"},

&nbsp;           files={"file": ("lifecycle.csv", BytesIO(csv\_content), "text/csv")},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert upload\_resp.status\_code == 200

&nbsp;       uploaded\_path = upload\_resp.json()\["path"]



&nbsp;       # 2. List — should appear

&nbsp;       list\_resp = await async\_client.get(

&nbsp;           "/api/files/list",

&nbsp;           params={"path": "lifecycle\_test", "area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert list\_resp.status\_code == 200

&nbsp;       names = \[f\["name"] for f in list\_resp.json()\["files"]]

&nbsp;       assert "lifecycle.csv" in names



&nbsp;       # 3. Download — content matches

&nbsp;       download\_resp = await async\_client.get(

&nbsp;           f"/api/files/download/{uploaded\_path}",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert download\_resp.status\_code == 200

&nbsp;       assert download\_resp.content == csv\_content



&nbsp;       # 4. Get URL

&nbsp;       url\_resp = await async\_client.get(

&nbsp;           f"/api/files/url/{uploaded\_path}",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert url\_resp.status\_code == 200

&nbsp;       assert "url" in url\_resp.json()



&nbsp;       # 5. Delete

&nbsp;       delete\_resp = await async\_client.delete(

&nbsp;           f"/api/files/{uploaded\_path}",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert delete\_resp.status\_code == 200



&nbsp;       # 6. Verify deleted

&nbsp;       verify\_resp = await async\_client.get(

&nbsp;           f"/api/files/download/{uploaded\_path}",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert verify\_resp.status\_code == 404



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_cross\_area\_isolation(self, async\_client, admin\_token, override\_storage):

&nbsp;       """Files in inputs should not be accessible from outputs area."""

&nbsp;       # test\_loans.csv exists in inputs

&nbsp;       inputs\_resp = await async\_client.get(

&nbsp;           "/api/files/download/test\_loans.csv",

&nbsp;           params={"area": "inputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert inputs\_resp.status\_code == 200



&nbsp;       # Same file should NOT exist in outputs

&nbsp;       outputs\_resp = await async\_client.get(

&nbsp;           "/api/files/download/test\_loans.csv",

&nbsp;           params={"area": "outputs"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert outputs\_resp.status\_code == 404





Test Suite: backend/tests/test\_storage\_local.py



python

"""

Unit tests for LocalStorage backend.

Tests storage operations directly without going through API routes.

"""

import pytest

from pathlib import Path

from io import BytesIO

from fastapi import UploadFile



from backend.storage.local import LocalStorage



@pytest.fixture

def local\_storage(tmp\_path) -> LocalStorage:

&nbsp;   storage = LocalStorage(base\_path=str(tmp\_path))

&nbsp;   # Seed test data

&nbsp;   inputs = tmp\_path / "inputs"

&nbsp;   (inputs / "test.csv").write\_text("a,b\\n1,2\\n")

&nbsp;   (inputs / "subdir").mkdir()

&nbsp;   (inputs / "subdir" / "nested.csv").write\_text("x,y\\n3,4\\n")

&nbsp;   return storage



class TestLocalStorageList:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_root(self, local\_storage):

&nbsp;       files = await local\_storage.list\_files("", area="inputs")

&nbsp;       names = \[f\["name"] for f in files]

&nbsp;       assert "test.csv" in names

&nbsp;       assert "subdir" in names



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_recursive(self, local\_storage):

&nbsp;       files = await local\_storage.list\_files("", recursive=True, area="inputs")

&nbsp;       paths = \[f\["path"] for f in files]

&nbsp;       assert any("nested.csv" in p for p in paths)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_empty\_dir(self, local\_storage):

&nbsp;       files = await local\_storage.list\_files("nonexistent", area="inputs")

&nbsp;       assert files == \[]



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_file\_metadata(self, local\_storage):

&nbsp;       files = await local\_storage.list\_files("", area="inputs")

&nbsp;       csv\_file = next(f for f in files if f\["name"] == "test.csv")

&nbsp;       assert csv\_file\["type"] == "file"

&nbsp;       assert csv\_file\["size"] > 0

&nbsp;       assert "last\_modified" in csv\_file



class TestLocalStorageUpload:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload(self, local\_storage):

&nbsp;       content = b"col1,col2\\nval1,val2\\n"

&nbsp;       upload = UploadFile(filename="uploaded.csv", file=BytesIO(content))

&nbsp;       result = await local\_storage.upload\_file(upload, "", area="inputs")

&nbsp;       assert result\["status"] == "uploaded"

&nbsp;       assert result\["size"] == len(content)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_to\_subdir(self, local\_storage):

&nbsp;       content = b"data"

&nbsp;       upload = UploadFile(filename="deep.csv", file=BytesIO(content))

&nbsp;       result = await local\_storage.upload\_file(upload, "new/deep/path", area="inputs")

&nbsp;       assert "new/deep/path" in result\["path"] or "deep.csv" in result\["path"]



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload\_bad\_extension(self, local\_storage):

&nbsp;       upload = UploadFile(filename="bad.exe", file=BytesIO(b"malware"))

&nbsp;       with pytest.raises(ValueError, match="not allowed"):

&nbsp;           await local\_storage.upload\_file(upload, "", area="inputs")



class TestLocalStorageDownload:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download(self, local\_storage):

&nbsp;       response = await local\_storage.download\_file("test.csv", area="inputs")

&nbsp;       assert response.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_not\_found(self, local\_storage):

&nbsp;       from fastapi import HTTPException

&nbsp;       with pytest.raises(HTTPException) as exc\_info:

&nbsp;           await local\_storage.download\_file("nonexistent.csv", area="inputs")

&nbsp;       assert exc\_info.value.status\_code == 404



class TestLocalStorageDelete:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_delete(self, local\_storage):

&nbsp;       # Upload then delete

&nbsp;       upload = UploadFile(filename="temp.csv", file=BytesIO(b"temp"))

&nbsp;       await local\_storage.upload\_file(upload, "", area="inputs")

&nbsp;       result = await local\_storage.delete\_file("temp.csv", area="inputs")

&nbsp;       assert result\["status"] == "deleted"



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_delete\_not\_found(self, local\_storage):

&nbsp;       from fastapi import HTTPException

&nbsp;       with pytest.raises(HTTPException) as exc\_info:

&nbsp;           await local\_storage.delete\_file("ghost.csv", area="inputs")

&nbsp;       assert exc\_info.value.status\_code == 404



class TestLocalStorageMkdir:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_create\_directory(self, local\_storage):

&nbsp;       result = await local\_storage.create\_directory("new\_dir", area="inputs")

&nbsp;       assert result\["status"] == "created"



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_create\_existing\_directory(self, local\_storage):

&nbsp;       result = await local\_storage.create\_directory("subdir", area="inputs")

&nbsp;       assert result\["status"] == "exists"



class TestLocalStoragePathSecurity:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_traversal\_in\_list(self, local\_storage):

&nbsp;       from fastapi import HTTPException

&nbsp;       with pytest.raises((HTTPException, ValueError)):

&nbsp;           await local\_storage.list\_files("../../etc", area="inputs")



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_traversal\_in\_download(self, local\_storage):

&nbsp;       from fastapi import HTTPException

&nbsp;       with pytest.raises((HTTPException, ValueError)):

&nbsp;           await local\_storage.download\_file("../../etc/passwd", area="inputs")



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_traversal\_in\_upload(self, local\_storage):

&nbsp;       upload = UploadFile(filename="test.csv", file=BytesIO(b"data"))

&nbsp;       with pytest.raises((HTTPException, ValueError)):

&nbsp;           await local\_storage.upload\_file(upload, "../../escape", area="inputs")





Test Suite: backend/tests/test\_storage\_s3.py



python

"""

Unit tests for S3Storage backend using mocked boto3.

Tests S3 operations without requiring AWS credentials.

"""

import pytest

from unittest.mock import MagicMock, patch

from io import BytesIO

from fastapi import UploadFile



from backend.storage.s3 import S3Storage



@pytest.fixture

def mock\_s3\_client():

&nbsp;   with patch("backend.storage.s3.boto3") as mock\_boto3:

&nbsp;       mock\_client = MagicMock()

&nbsp;       mock\_boto3.client.return\_value = mock\_client

&nbsp;       yield mock\_client



@pytest.fixture

def s3\_storage(mock\_s3\_client) -> S3Storage:

&nbsp;   return S3Storage(

&nbsp;       bucket\_name="test-bucket",

&nbsp;       region="us-east-1",

&nbsp;       aws\_access\_key\_id="test-key",

&nbsp;       aws\_secret\_access\_key="test-secret",

&nbsp;   )



class TestS3StorageList:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_files(self, s3\_storage, mock\_s3\_client):

&nbsp;       mock\_paginator = MagicMock()

&nbsp;       mock\_s3\_client.get\_paginator.return\_value = mock\_paginator

&nbsp;       mock\_paginator.paginate.return\_value = \[

&nbsp;           {

&nbsp;               "Contents": \[

&nbsp;                   {

&nbsp;                       "Key": "inputs/test.csv",

&nbsp;                       "Size": 1024,

&nbsp;                       "LastModified": "2026-02-20T12:00:00Z",

&nbsp;                   },

&nbsp;               ],

&nbsp;               "CommonPrefixes": \[

&nbsp;                   {"Prefix": "inputs/subdir/"},

&nbsp;               ],

&nbsp;           }

&nbsp;       ]



&nbsp;       files = await s3\_storage.list\_files("", area="inputs")

&nbsp;       assert len(files) == 2

&nbsp;       assert files\[0]\["name"] == "test.csv"

&nbsp;       assert files\[1]\["name"] == "subdir"

&nbsp;       assert files\[1]\["type"] == "directory"



class TestS3StorageUpload:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_upload(self, s3\_storage, mock\_s3\_client):

&nbsp;       content = b"col1,col2\\nval1,val2\\n"

&nbsp;       upload = UploadFile(filename="upload.csv", file=BytesIO(content))



&nbsp;       result = await s3\_storage.upload\_file(upload, "", area="inputs")



&nbsp;       mock\_s3\_client.put\_object.assert\_called\_once()

&nbsp;       call\_kwargs = mock\_s3\_client.put\_object.call\_args\[1]

&nbsp;       assert call\_kwargs\["Bucket"] == "test-bucket"

&nbsp;       assert "inputs" in call\_kwargs\["Key"]

&nbsp;       assert result\["status"] == "uploaded"



class TestS3StorageDownload:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download(self, s3\_storage, mock\_s3\_client):

&nbsp;       mock\_body = MagicMock()

&nbsp;       mock\_body.read.side\_effect = \[b"csv content", b""]

&nbsp;       mock\_s3\_client.get\_object.return\_value = {

&nbsp;           "Body": mock\_body,

&nbsp;           "ContentLength": 11,

&nbsp;       }



&nbsp;       response = await s3\_storage.download\_file("test.csv", area="inputs")

&nbsp;       assert response.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_download\_not\_found(self, s3\_storage, mock\_s3\_client):

&nbsp;       from botocore.exceptions import ClientError

&nbsp;       mock\_s3\_client.get\_object.side\_effect = ClientError(

&nbsp;           {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},

&nbsp;           "GetObject",

&nbsp;       )



&nbsp;       from fastapi import HTTPException

&nbsp;       with pytest.raises(HTTPException) as exc\_info:

&nbsp;           await s3\_storage.download\_file("nonexistent.csv", area="inputs")

&nbsp;       assert exc\_info.value.status\_code == 404



class TestS3StoragePresignedUrl:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_presigned\_url(self, s3\_storage, mock\_s3\_client):

&nbsp;       mock\_s3\_client.head\_object.return\_value = {}

&nbsp;       mock\_s3\_client.generate\_presigned\_url.return\_value = "https://s3.example.com/signed"



&nbsp;       url = await s3\_storage.get\_presigned\_url("test.csv", area="inputs")

&nbsp;       assert url.startswith("https://")

&nbsp;       mock\_s3\_client.generate\_presigned\_url.assert\_called\_once()



class TestS3StorageDelete:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_delete(self, s3\_storage, mock\_s3\_client):

&nbsp;       mock\_s3\_client.head\_object.return\_value = {}

&nbsp;       result = await s3\_storage.delete\_file("test.csv", area="inputs")

&nbsp;       assert result\["status"] == "deleted"

&nbsp;       mock\_s3\_client.delete\_object.assert\_called\_once()





Validation Criteria for Phase 3



After implementation, ALL must pass:

1\. uvicorn starts without errors

2\. LocalStorage: list, upload, download, delete, mkdir all work

3\. S3Storage: all operations work with mocked boto3

4\. Path traversal attempts (../../) are blocked at every endpoint

5\. Invalid storage areas are rejected with 400

6\. File extension validation blocks .exe, .sh, .bat etc.

7\. GET /api/files/list returns file metadata (name, size, type, last\_modified)

8\. POST /api/files/upload stores files correctly

9\. GET /api/files/download/{path} returns file content with correct Content-Type

10\. GET /api/files/url/{path} returns URL/path for file access

11\. DELETE /api/files/{path} removes files, returns 404 for missing files

12\. POST /api/files/mkdir creates directories, is idempotent

13\. Cross-area isolation: inputs files not accessible from outputs area

14\. Full lifecycle test: upload → list → download → delete works end-to-end

15\. Unauthenticated requests return 401

16\. pytest backend/tests/test\_file\_routes.py — all tests pass

17\. pytest backend/tests/test\_storage\_local.py — all tests pass

18\. pytest backend/tests/test\_storage\_s3.py — all tests pass

19\. ruff check backend/storage/ backend/api/files.py backend/utils/ — no lint errors



Run validation:



bash

pytest backend/tests/test\_file\_routes.py backend/tests/test\_storage\_local.py backend/tests/test\_storage\_s3.py -v --tb=short

ruff check backend/storage/ backend/api/files.py backend/utils/





Chunking Guide (if prompt exceeds context limits)



| Chunk | File(s) | Focus |

|-------|---------|-------|

| 3a | backend/utils/path\_utils.py | Path security utilities |

| 3b | backend/storage/local.py | Local filesystem backend |

| 3c | backend/storage/s3.py | S3 backend |

| 3d | backend/api/files.py | API route implementations |

| 3e | backend/tests/test\_storage\_local.py | Local storage unit tests |

| 3f | backend/tests/test\_storage\_s3.py | S3 storage unit tests |

| 3g | backend/tests/test\_file\_routes.py | API route integration tests |



Prepend specs/context/project-context.md + specs/context/phase2-output-summary.md

to each chunk.



