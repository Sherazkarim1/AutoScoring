from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.auth import get_current_instructor
from app.config import settings
from app.models import Instructor

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{filename}")
def get_uploaded_file(
    filename: str,
    _: Instructor = Depends(get_current_instructor),
):
    upload_dir = Path(settings.upload_dir).resolve()
    file_path = (upload_dir / filename).resolve()

    if not str(file_path).startswith(str(upload_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
