from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# ─────────────────────────────────────────────
# APP INIT
# ─────────────────────────────────────────────

app = FastAPI(
    title="Gemini Multi-Agent API",
    description=(
        "A production-grade multi-agent AI system that processes meeting transcripts "
        "end-to-end using 3 specialized Gemini agents coordinated by LangGraph."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI  → http://localhost:8000/docs
    redoc_url="/redoc"      # ReDoc UI    → http://localhost:8000/redoc
)

# ─────────────────────────────────────────────
# CORS — allows frontend or Postman to call the API
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# REGISTER ROUTES
# ─────────────────────────────────────────────

app.include_router(router, prefix="/api/v1")


# ─────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "project": "Gemini Multi-Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }