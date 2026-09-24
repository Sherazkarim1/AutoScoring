from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.auth import get_current_instructor
from app.models import Instructor
from app.services.storage import get_file_storage

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{filename}")
def get_uploaded_file(
    filename: str,
    _: Instructor = Depends(get_current_instructor),
):
    try:
        content = get_file_storage().read(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid file path") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc

    return Response(
        content=content,
        media_type=get_file_storage().media_type(filename),
    )
