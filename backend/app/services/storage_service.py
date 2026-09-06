from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

READ_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class StoredUpload:
    original_name: str
    path: Path
    mime_type: str
    size: int
    checksum_sha256: str


async def store_upload(upload: UploadFile, *folder_parts: str) -> StoredUpload:
    """Stream an upload to a temporary file, enforce its limit, then publish it."""

    original_name = Path(upload.filename or "document.bin").name
    suffix = Path(original_name).suffix[:16]
    folder = settings.storage_root.joinpath(*folder_parts)
    folder.mkdir(parents=True, exist_ok=True)

    final_path = folder / f"{uuid4().hex}{suffix}"
    temporary_path = final_path.with_suffix(f"{final_path.suffix}.part")
    digest = sha256()
    size = 0

    try:
        with temporary_path.open("xb") as destination:
            while chunk := await upload.read(READ_CHUNK_SIZE):
                size += len(chunk)
                if size > settings.max_upload_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            "File exceeds the configured "
                            f"{settings.max_upload_size_mb} MB upload limit"
                        ),
                    )
                destination.write(chunk)
                digest.update(chunk)

        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty",
            )
        temporary_path.replace(final_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    return StoredUpload(
        original_name=original_name,
        path=final_path,
        mime_type=upload.content_type or "application/octet-stream",
        size=size,
        checksum_sha256=digest.hexdigest(),
    )


def remove_stored_upload(stored: StoredUpload) -> None:
    """Compensate for a failed database transaction after file storage."""

    stored.path.unlink(missing_ok=True)
