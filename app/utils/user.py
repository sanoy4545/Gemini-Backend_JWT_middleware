from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.db import get_db

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    mobile = getattr(request.state, "user_mobile", None)
    result = await db.execute(select(User).where(User.mobile == mobile))
    user = result.scalars().first()
    return user
