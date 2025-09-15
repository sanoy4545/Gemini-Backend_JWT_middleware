from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.models.user import User
from app.utils.user import get_current_user

router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.get("/status", response_class=JSONResponse)
async def subscription_status(current_user: User = Depends(get_current_user)):
    return {"success": True, "subscription": current_user.subscription}
