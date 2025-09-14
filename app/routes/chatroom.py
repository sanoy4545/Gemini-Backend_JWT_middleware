from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.chatroom import Chatroom
from app.routes.auth import get_current_user
from app.schemas import ChatroomCreate
from app.schemas_chatroom import ChatroomOut
from app.core.redis_client import redis_client
import json
from fastapi.responses import JSONResponse
from app.models.message import Message
from app.utils.queue import enqueue_gemini_task
from app.models.user import User
from app.schemas import MessageCreate
from sqlalchemy import select
from datetime import datetime

router = APIRouter(prefix="/chatroom", tags=["chatroom"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_class=JSONResponse)
async def create_chatroom(data: ChatroomCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require authentication
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Uauthorized"})
    # Create new chatroom for user
    chatroom = Chatroom(name=data.name, user_id=current_user.id)
    db.add(chatroom)
    await db.commit()
    await db.refresh(chatroom)
    return JSONResponse(status_code=201, content={"success": True, "chatroom_id": chatroom.id, "name": chatroom.name})


@router.get("/", response_class=JSONResponse)
async def list_chatrooms(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require authentication
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    cache_key = f"chatrooms:{current_user.id}"
    cached = await redis_client.get(cache_key)
    if cached:
        chatrooms = json.loads(cached)
        return JSONResponse(status_code=200, content={"success": True, "chatrooms": chatrooms, "cached": True})
    # Not cached, fetch from DB
    from sqlalchemy import select
    result = await db.execute(
        select(Chatroom).where(Chatroom.user_id == current_user.id)
    )
    chatrooms = [
        {"id": row.id, "name": row.name, "created_at": row.created_at.isoformat()} for row in result.scalars().all()
    ]
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(chatrooms))
    return JSONResponse(status_code=200, content={"success": True, "chatrooms": chatrooms})


@router.get("/{chatroom_id}", response_class=JSONResponse)
async def get_chatroom(chatroom_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require authentication
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    # Fetch chatroom by id and user
    result = await db.execute(
        Chatroom.__table__.select().where(
            (Chatroom.id == chatroom_id) & (Chatroom.user_id == current_user.id)
        )
    )
    row = result.first()
    if not row:
        return JSONResponse(status_code=404, content={"success": False, "message": "Chatroom not found"})
    chatroom = row[0] if isinstance(row, tuple) else row
    return JSONResponse(status_code=200, content={
        "success": True,
        "chatroom": {
            "id": chatroom.id,
            "name": chatroom.name,
            "created_at": chatroom.created_at.isoformat()
        }
    })


@router.post("/{chatroom_id}/message", response_class=JSONResponse)
async def post_message(chatroom_id: int, data: MessageCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require authentication
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    # Get chatroom by chatroom_id and user
    result = await db.execute(select(Chatroom).where((Chatroom.id == chatroom_id) & (Chatroom.user_id == current_user.id)))
    chatroom = result.scalars().first()
    if not chatroom:
        return JSONResponse(status_code=404, content={"success": False, "message": "Chatroom not found"})
    user = current_user
    # Save user message to DB
    message = Message(chatroom_id=chatroom.id, sender="user", content=data.content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    # Enqueue Gemini API task
    await enqueue_gemini_task(chatroom.id, user.id, message.id, data.content)
    # Wait for Gemini response (poll for new AI message)
    from asyncio import sleep
    ai_message = None
    for _ in range(40):  # Wait up to ~20 seconds (40 x 0.5s)
        async with AsyncSessionLocal() as poll_db:
            result = await poll_db.execute(
                select(Message).where(
                    (Message.chatroom_id == chatroom.id) & (Message.sender == "ai")
                ).order_by(Message.created_at.desc())
            )
            ai_message = result.scalars().first()
        if ai_message and ai_message.created_at > message.created_at:
            break
        await sleep(0.5)
    # Only increment usage if Gemini response is valid
    if ai_message and ai_message.created_at > message.created_at and ai_message.content and not ai_message.content.startswith("[Gemini API error"):
        if current_user.subscription.lower() == "basic":
            today = datetime.utcnow().strftime("%Y-%m-%d")
            redis_key = f"usage:{user.id}:{today}"
            usage = await redis_client.get(redis_key)
            usage = int(usage) if usage else 0
            if usage >= 5:
                return JSONResponse(status_code=429, content={"success": False, "message": "Daily message limit reached for Basic plan. Upgrade to Pro for more usage."})
            await redis_client.incr(redis_key)
            await redis_client.expire(redis_key, 86400)  # 1 day
    if not ai_message or ai_message.created_at <= message.created_at:
        return JSONResponse(status_code=202, content={"success": True, "message_id": message.id, "status": "queued", "ai_message": None, "info": "AI response not ready yet. Try again soon."})
    return JSONResponse(status_code=200, content={
        "success": True,
        "message_id": message.id,
        "ai_message": ai_message.content
    })
