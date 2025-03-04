from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Shared Attributes


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None  # Email is nullable in your model

# user only gives un username, email and password and we only need to validate these 3 fields


class UserCreate(UserBase):
    hashed_password: str  # Plain password for user registration

# we need to send id, username, email, created_at fields when returning user info


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_verified: Optional[bool] = False
    # Allows SQLAlchemy models to be converted to Pydantic

    class Config:
        orm_mode = True


class OTPCreate(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str
