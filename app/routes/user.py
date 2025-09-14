from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.routes.auth import get_current_user
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/user", tags=["user"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/me", response_class=JSONResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    return JSONResponse(status_code=200, content={
        "success": True,
        "id": current_user.id,
        "mobile": current_user.mobile,
        "name": current_user.name
    })
