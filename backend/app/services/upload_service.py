import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ..config import MAX_IMAGE_BYTES, MAX_VIDEO_BYTES, UPLOAD_DIR

SIGNATURES = {
    ".jpg": ("image", "image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    ".jpeg": ("image", "image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    ".png": ("image", "image/png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    ".webp": ("image", "image/webp", lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    ".mp4": ("video", "video/mp4", lambda b: len(b) >= 8 and b[4:8] == b"ftyp"),
    ".webm": ("video", "video/webm", lambda b: b.startswith(b"\x1a\x45\xdf\xa3")),
}


async def store_upload(file: UploadFile):
    extension = Path(file.filename or "").suffix.lower()
    signature = SIGNATURES.get(extension)
    if signature is None:
        raise HTTPException(400, detail={"detail": "Unsupported media extension", "code": "invalid_media"})
    media_type, expected_mime, matches = signature
    if file.content_type and file.content_type.lower() != expected_mime:
        raise HTTPException(400, detail={"detail": "Media MIME type does not match its extension", "code": "invalid_media_mime"})
    max_bytes = MAX_IMAGE_BYTES if media_type == "image" else MAX_VIDEO_BYTES
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / safe_name
    size = 0
    header = b""
    try:
        with destination.open("wb") as target:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(413, detail={"detail": "Media exceeds the configured size limit", "code": "media_too_large"})
                if len(header) < 16:
                    header += chunk[:16 - len(header)]
                target.write(chunk)
        if not matches(header):
            raise HTTPException(400, detail={"detail": "File content does not match its extension", "code": "invalid_media_content"})
        return safe_name, media_type, size
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
