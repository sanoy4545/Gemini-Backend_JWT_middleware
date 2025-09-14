from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User
from fastapi import HTTPException, status
from app.schemas import UserSignup, OTPRequest, OTPVerify, ChangePassword
from app.utils.jwt import create_access_token, verify_access_token
from app.core.redis_client import redis_client
from passlib.context import CryptContext
import random
from fastapi.responses import JSONResponse
from fastapi import Header, Request
from sqlalchemy import select


router = APIRouter(prefix='/auth', tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        
        
# Dependency to get current user from JWT
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload or "sub" not in payload:
        return None
    mobile = payload["sub"]
    result = await db.execute(select(User).where(User.mobile == mobile))
    user = result.scalars().first()
    return user


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    range_start = 10**(length-1)
    range_end = (10**length)-1
    return str(random.randint(range_start, range_end))






@router.post("/signup", response_class=JSONResponse)
async def signup(user: UserSignup, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(
        User.__table__.select().where(User.mobile == user.mobile)
    )
    existing = result.first()
    if existing:
        return JSONResponse(status_code=409, content={"success": False, "message": "User already exists"})
    # Hash password and create new user
    password_hash = pwd_context.hash(user.password) if user.password else None
    new_user = User(mobile=user.mobile, name=user.name, password_hash=password_hash)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return JSONResponse(status_code=201, content={"success": True, "id": new_user.id, "mobile": new_user.mobile, "name": new_user.name})


@router.post("/send-otp", response_class=JSONResponse)
async def send_otp(data: OTPRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(
        User.__table__.select().where(User.mobile == data.mobile)
    )
    user = result.first()
    if not user:
        return JSONResponse(status_code=404, content={"success": False, "message": "Mobile number not registered"})
    # Generate OTP and store in Redis for login/verification
    otp = generate_otp()
    await redis_client.setex(f"otp:{data.mobile}", 300, otp)
    return JSONResponse(status_code=200, content={"success": True, "mobile": data.mobile, "otp": otp})



@router.post("/verify-otp", response_class=JSONResponse)
async def verify_otp(data: OTPVerify):
    # Retrieve OTP from Redis and verify
    otp_in_redis = await redis_client.get(f"otp:{data.mobile}")
    if not otp_in_redis or otp_in_redis != data.otp:
        return JSONResponse(status_code=400, content={"success": False, "message": "Invalid or expired OTP"})
    await redis_client.delete(f"otp:{data.mobile}")
    # Issue JWT token on success
    token = create_access_token({"sub": data.mobile})
    return JSONResponse(status_code=200, content={"success": True, "access_token": token, "token_type": "bearer"})




@router.post("/forgot-password", response_class=JSONResponse)
async def forgot_password(data: OTPRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(
        User.__table__.select().where(User.mobile == data.mobile)
    )
    user = result.first()
    if not user:
        return JSONResponse(status_code=404, content={"success": False, "message": "Mobile number not registered"})
    # Generate OTP and store in Redis for password reset
    otp = generate_otp()
    await redis_client.setex(f"reset_otp:{data.mobile}", 300, otp)
    return JSONResponse(status_code=200, content={"success": True, "mobile": data.mobile, "otp": otp})



@router.post("/change-password", response_class=JSONResponse)
async def change_password(data: ChangePassword, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require authentication
    if not current_user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    # If old_password is provided, check it
    if data.old_password:
        if not current_user.password_hash or not pwd_context.verify(data.old_password, current_user.password_hash):
            return JSONResponse(status_code=400, content={"success": False, "message": "Old password is incorrect"})
    # Update password
    current_user.password_hash = pwd_context.hash(data.new_password)
    db.add(current_user)
    await db.commit()
    return JSONResponse(status_code=200, content={"success": True, "message": "Password changed successfully"})