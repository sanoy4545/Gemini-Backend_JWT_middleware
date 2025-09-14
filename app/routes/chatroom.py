
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

router = APIRouter(prefix="/chatroom", tags=["chatroom"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_class=JSONResponse)
async def create_chatroom(data: ChatroomCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require authentication
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
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
    result = await db.execute(
        Chatroom.__table__.select().where(Chatroom.user_id == current_user.id)
    )
    chatrooms = [
        {"id": row.id, "name": row.name, "created_at": row.created_at.isoformat()} for row in result.scalars().all()
    ]
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(chatrooms))
    return JSONResponse(status_code=200, content={"success": True, "chatrooms": chatrooms, "cached": False})

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
