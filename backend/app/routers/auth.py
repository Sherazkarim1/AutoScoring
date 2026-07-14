from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_instructor, get_password_hash, verify_password
from app.database import get_db
from app.models import Instructor
from app.schemas import InstructorCreate, InstructorOut, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=InstructorOut, status_code=status.HTTP_201_CREATED)
def register(payload: InstructorCreate, db: Session = Depends(get_db)):
    existing = db.query(Instructor).filter(Instructor.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    instructor = Instructor(
        name=payload.name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    return instructor


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    instructor = db.query(Instructor).filter(Instructor.email == form_data.username).first()
    if not instructor or not verify_password(form_data.password, instructor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(instructor.id)})
    return Token(access_token=token)


@router.get("/me", response_model=InstructorOut)
def get_me(current: Instructor = Depends(get_current_instructor)):
    return current
