from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import setup_logging
from routers import document, healthcheck, query

setup_logging()

app = FastAPI(
    title=settings.app_name,
    description="PDF Document QA with RAG using OpenAI",
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthcheck.router)
app.include_router(document.router)
app.include_router(query.router)
