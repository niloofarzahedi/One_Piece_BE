from fastapi import APIRouter, WebSocket, Depends, WebSocketException, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.chat import ChatRoom, ChatParticipant, ChatMessage
from app.schemas.chat import ChatCreate, ChatResponse, MessageResponse
from sqlalchemy.future import select
from datetime import datetime


router = APIRouter()


@router.get("/", response_model=list[ChatResponse])
async def get_user_chats(username: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        # Retrieve list of chats for the authenticated user
        # check user exists
        result = await db.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        chat_result = await db.execute(select(ChatRoom).join(ChatParticipant).filter(ChatParticipant.user_id == user.id))
        chats = chat_result.scalars().all()
        if chats is None:
            raise HTTPException(status_code=404, detail="No chats found")
        chat_responses = [
            ChatResponse(
                id=chat.id,
                name=chat.name,
                is_group=chat.is_group,
                created_at=chat.created_at
            ) for chat in chats
        ]
        return chat_responses
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/create", response_model=ChatResponse)
async def create_chat(chat: ChatCreate, username: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        # Create a new chat
        new_chat = ChatRoom(name=chat.name, is_group=chat.is_group)
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)

        chat_data = ChatResponse(
            id=new_chat.id,
            name=new_chat.name,
            is_group=new_chat.is_group,
            created_at=new_chat.created_at
        )

        # Get the authenticated user
        result = await db.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        print("user", user)

        # Add the user as a chat participant
        participant = ChatParticipant(chat_id=new_chat.id, user_id=user.id)
        db.add(participant)
        await db.commit()
        await db.refresh(participant)
        print("participant", participant)

        # Return a Pydantic model, not a database model
        return chat_data

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(chat_id: int, username: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        # Retrieve messages for a given chat (only if the user is a participant)
        chat_result = await db.execute(select(ChatRoom).filter(ChatRoom.id == chat_id))
        chat = chat_result.scalars().first()
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        user_result = await db.execute(select(User).filter(User.username == username))
        user = user_result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        is_participant = await db.execute(
            select(ChatParticipant).filter(ChatParticipant.chat_id ==
                                           chat_id, ChatParticipant.user_id == user.id))
        if not is_participant:
            raise HTTPException(
                status_code=403, detail="Not authorized for this chat")

        messages_result = await db.execute(
            select(ChatMessage).filter(ChatMessage.chat_id == chat_id)
        )
        messages = messages_result.scalars().all()
        if messages is None:
            raise HTTPException(status_code=404, detail="No messages found")

        message_responses = [
            MessageResponse(
                chat_id=message.chat_id,
                sender_id=message.sender_id,
                message=message.message
            ) for message in messages
        ]
        return message_responses
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db), username: str = Depends(get_current_user)):
    """Restrict WebSocket access to authenticated users."""
    try:
        if username is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        user = await db.execute(select(User).filter(User.username == username)).scalars().first()
        if user is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        # Accept connection after authentication check
        await websocket.accept()
        print("successful connection")

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")

    except WebSocketException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
