import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from .database.db import init_db
from .retrieval.hybrid_search import sync_bm25_index
from .api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and sync BM25 index
    init_db()
    sync_bm25_index()
    print("Backend initialized successfully. SQLite, BM25, and Vector Store ready.")
    yield

app = FastAPI(
    title="Enterprise Documentation Q&A Assistant API",
    description="Evidence-Grounded Retrieval-Augmented Generation (RAG) System for Enterprise Documentation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Mount frontend production build if available
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    # Serve static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)
