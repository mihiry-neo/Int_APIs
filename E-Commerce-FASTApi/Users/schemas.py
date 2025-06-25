from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
 
class UserBase(BaseModel):
    username: str
    email: EmailStr
    gender: str
    age: int
    phone_number: str
    nationality: str
    is_active: Optional[bool] = True
 
class UserCreate(UserBase):
    password: str
 
class UserOut(UserBase):
    user_id: int  # ✅ match SQLAlchemy model field name
 
    class Config:
        from_attributes = True  # Enables ORM conversion
 
class UserLogin(BaseModel):
    email: EmailStr
    password: str