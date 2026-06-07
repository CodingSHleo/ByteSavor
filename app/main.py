import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
from app.core.database import engine, Base, async_session
from app.models.recipe import Recipe  # noqa: 注册 ORM
from app.routers import sense, decision, task, agent, feedback, user, auth, assistant, quality, nutrition, guide

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.config import settings
    if not settings.jwt_secret:
        logger.warning("JWT_SECRET 未设置！请修改 .env 中的 JWT_SECRET")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with async_session() as db:
            from app.seed.seed_recipes import seed
            await seed(db)
        logger.info("startup: tables created, seed loaded")
    except Exception as e:
        logger.warning("startup: db unavailable, skipping init (%s)", e)
    yield


app = FastAPI(
    title="ByteSavor V3.0 API",
    description="Full-chain AI Agent for food perception, decision and execution",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    from app.core.config import settings
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {"code": "INTERNAL_ERROR", "message": str(exc) if settings.debug else "服务器内部错误"},
            "trace_id": uuid.uuid4().hex,
        },
    )


app.include_router(auth.router)
app.include_router(sense.router)
app.include_router(decision.router)
app.include_router(task.router)
app.include_router(agent.router)
app.include_router(feedback.router)
app.include_router(user.router)
app.include_router(assistant.router)
app.include_router(quality.router)
app.include_router(nutrition.router)
app.include_router(guide.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
