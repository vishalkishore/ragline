from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logger import setup_logging
from routers import healthcheck

setup_logging()

app = FastAPI(title="Financial Analysis Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthcheck.router, prefix="/api")
