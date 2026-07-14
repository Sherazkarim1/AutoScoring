from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, dashboard, files, questions
from app.services.scoring import get_scoring_service
from migrate import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations()
    get_scoring_service()
    yield


app = FastAPI(
    title="AutoScoring API",
    description="Automatic Subjective Questions Scoring System using NLP and Deep Learning",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(files.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AutoScoring API"}
