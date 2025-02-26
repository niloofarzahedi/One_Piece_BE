from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# shared attributes


class BaseSchema(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Schema for creating a chat


class ChatCreate(BaseModel):
    name: Optional[str] = None  # Name is optional for private chats
    is_group: bool

    class Config:
        from_attributes = True

# Schema for returning chat details


class ChatResponse(BaseModel):
    id: int
    name: str | None  # Can be None for private chats
    is_group: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Schema for sending a message


class MessageCreate(BaseModel):
    chat_id: int
    message: str

# Schema for returning a message


class MessageResponse(BaseSchema):
    chat_id: int
    sender_id: int
    message: str

# Schema for listing chats


class ChatListResponse(BaseModel):
    chats: List[ChatResponse]

# Schema for listing messages in a chat


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
