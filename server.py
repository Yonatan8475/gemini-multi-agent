from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from database.db import init_db

app = FastAPI(
    title="Gemini Multi-Agent API",
    description="Meeting transcript processor with 3 AI agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

# Include routes
app.include_router(router, prefix="/api")

# Health check
@app.get("/")
def root():
    return {"status": "running", "message": "Gemini Multi-Agent API is live"}