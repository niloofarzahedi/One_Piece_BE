from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User, OTP
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.security import verify_password
from app.core.email import send_otp_email
from app.core.jwt import create_access_token, create_refresh_token, verify_refresh_token
from app.dependencies.auth import get_current_user
import random

router = APIRouter()


# you can use get_current_user for each api that needs user authentication
@router.get("/me")
async def get_me(username: str = Depends(get_current_user)):
    return {"username": username}


@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.username == form_data.username))
        user = result.scalars().first()
        # check the provided pass with its hash
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Invalid username or password")

        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # check user exists
        result = await db.execute(select(User).filter(User.username == user.username))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=400, detail="Username already registered")
        # Hash the password before saving
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.hashed_password)
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        user_data = UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            created_at=new_user.created_at
        )

        # # Generate a random 6-digit OTP
        # otp_code = str(random.randint(100000, 999999))

        # # Store OTP (ensure user_id is the primary key)
        # existing_otp = await db.execute(select(OTP).filter(OTP.user_id == new_user.id))
        # otp_entry = existing_otp.scalars().first()

        # if otp_entry:
        #     otp_entry.otp_code = otp_code
        # else:
        #     new_otp = OTP(user_id=new_user.id, otp_code=otp_code)
        #     db.add(new_otp)

        # await db.commit()

        # # Send OTP via email
        # await send_otp_email(user.email, otp_code)

        return user_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=401, detail="Invalid or expired refresh token")

        new_access_token = create_access_token({"sub": payload["sub"]})

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
