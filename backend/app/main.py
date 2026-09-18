from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, knowledge, sites
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.knowledge.loader import load_knowledge_base
from app.knowledge.search import get_chunk_index

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        load_knowledge_base(db)
        get_chunk_index().build(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="TerraSense API",
    description="AI biodiversity intelligence chatbot for the Darukaa.Earth challenge",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(sites.router)
app.include_router(knowledge.router)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
