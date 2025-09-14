

from pydantic import BaseModel


class UserSignup(BaseModel):
    mobile: str
    name: str
    password: str = None

class OTPRequest(BaseModel):
    mobile: str
    
class OTPVerify(BaseModel):
    mobile: str
    otp: str

class ChangePassword(BaseModel):
    old_password: str = None
    new_password: str

class MessageCreate(BaseModel):
    content: str

class ChatroomCreate(BaseModel):
    name: str

