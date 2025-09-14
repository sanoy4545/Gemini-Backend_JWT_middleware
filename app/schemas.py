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

