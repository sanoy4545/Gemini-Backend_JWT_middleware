
from pydantic import BaseModel, Field

class UserSignup(BaseModel):
    mobile: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)

class OTPRequest(BaseModel):
    mobile: int = Field(..., gt=0)

class OTPVerify(BaseModel):
    mobile: int = Field(..., gt=0)
    otp: str = Field(..., min_length=4)

class ChangePassword(BaseModel):
    old_password: str = Field(None, min_length=6)
    new_password: str = Field(..., min_length=6)

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class ChatroomCreate(BaseModel):
    name: str = Field(..., min_length=1)

