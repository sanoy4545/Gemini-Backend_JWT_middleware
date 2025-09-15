from fastapi import FastAPI
from app.middleware import JWTAuthMiddleware, ErrorHandlerMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, AsyncSessionLocal, Base
from app.core.redis_client import redis_client

from app.routes import auth
from app.routes import user
from app.routes import chatroom
from app.routes import subscribe
from app.routes import webhook
from app.routes import subscription
from app.utils import jwt


app = FastAPI()
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(JWTAuthMiddleware)

@app.on_event("startup")
async def startup():
    # Create tables if not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Test Redis connection
    await redis_client.ping()


@app.get("/")
async def root():
    return {"message": "Gemini-style backend API"}


# Routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chatroom.router)
app.include_router(subscribe.router)
app.include_router(webhook.router)
app.include_router(subscription.router)
