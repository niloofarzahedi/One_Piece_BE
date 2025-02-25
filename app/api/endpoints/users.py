from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserResponse
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()


@router.get("/users/", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse(id=user.id, username=user.username, email=user.email, created_at=user.created_at) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user.id, username=user.username, email=user.email, created_at=user.created_at)


@router.post("/users/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(username=user.username,
                    email=user.email, hashed_password=user.hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
