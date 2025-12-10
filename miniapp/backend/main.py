import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.exceptions import DomainError
from core.responses import error_response, success_response
from db import close_engine
from routers.auth import router as auth_router
from routers.analysis_history import router as analysis_history_router
from routers.favorites import router as favorites_router
from routers.protocols import router as protocols_router
from routers.users import router as users_router
from routers.watchlist import router as watchlist_router

logger = logging.getLogger(__name__)

# Load env from repo root and local directory (if present)
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_engine()


app = FastAPI(
    title="DeFi Agent API",
    description="DeFi 投资分析 API，提供协议分析、收藏、监控等接口",
    version="0.1.0",
    contact={"name": "TradingAgents Team", "url": "https://github.com/TauricResearch/TradingAgents", "email": "dev@tradingagents.local"},
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Allow frontends (Telegram WebView + local dev) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(protocols_router)
app.include_router(analysis_history_router)
app.include_router(favorites_router)
app.include_router(watchlist_router)
app.include_router(users_router)


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return success_response({"status": "ok", "message": "DeFi Agent API is running"})



@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=exc.code, message=exc.message),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(code="ValidationError", message=str(exc)),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    status_code = exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
    return JSONResponse(
        status_code=status_code,
        content=error_response(
            code="HTTPException",
            message=str(exc.detail) if exc.detail else exc.detail,
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(code="InternalServerError", message="An unexpected error occurred"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
