"""FastAPI entrypoint. Wires CORS + routers. No business logic lives here."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import analyze, parse

app = FastAPI(title="Resume Intelligence Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse.router)
app.include_router(analyze.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
