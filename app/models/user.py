from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    password_hash = Column(String(128), nullable=True)
    subscription = Column(String(20), nullable=False, default="Basic", server_default="basic")
    created_at = Column(DateTime, default=func.now())
