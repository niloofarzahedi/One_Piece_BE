from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    username = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_verified = Column(Boolean, default=False, nullable=True)

    otps = relationship("OTP", back_populates="user",
                        cascade="all, delete-orphan")


class OTP(Base):
    __tablename__ = "otps"

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    otp_code = Column(String, nullable=False)

    # Relationship with User model
    user = relationship("User", back_populates="otps")
