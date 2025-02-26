from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, Depends, WebSocketException, status, HTTPException, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.chat import ChatRoom, ChatParticipant, ChatMessage
from app.schemas.chat import ChatCreate, ChatResponse, MessageResponse
from sqlalchemy.future import select
from datetime import datetime
import json
import os
from jose import JWTError, jwt


router = APIRouter()


load_dotenv()
# JWT Secret and Algorithm
SECRET_KEY = os.getenv("SECRET KEY", "").strip()
ALGORITHM = os.getenv("ALGORITHM")


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


@router.post("/{chat_id}/add_participant")
async def add_participant(chat_id: int, username: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        # Add a participant to an existing chat
        result = await db.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # check if chat exists
        chat_result = await db.execute(select(ChatRoom).filter(ChatRoom.id == chat_id))
        chat = chat_result.scalars().first()
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        # check if user is already a participant
        participant_result = await db.execute(select(ChatParticipant).filter(ChatParticipant.chat_id == chat_id, ChatParticipant.user_id == user.id))
        existing_participant = participant_result.scalars().first()
        if existing_participant:
            raise HTTPException(
                status_code=400, detail="User is already a participant in this chat")

        # Add the user as a chat participant
        participant = ChatParticipant(chat_id=chat_id, user_id=user.id)
        db.add(participant)
        await db.commit()
        await db.refresh(participant)
        return participant
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


async def get_current_user_from_token(token: str, db: AsyncSession):
    """Manually extracts the user from JWT token."""
    credentials_exception = WebSocketDisconnect(
        code=1008)  # Unauthorized WebSocket Disconnect
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

# Store active WebSocket connections
active_connections = {}


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    # WebSocket for authenticated users to send/receive messages
    # Authenticate user
    await websocket.accept()
    # Authenticate user from token
    user = await get_current_user_from_token(token, db)
    print(f"User {user.username} connected to WebSocket")

    if not user:
        await websocket.close()
        print(f"User {user.username} not found in database")
        return

    user_id = user.id
    active_connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")
            message_data = json.loads(data)
            chat_id = message_data.get("chat_id")
            message_text = message_data.get("message")

            # Verify user is in the chat
            result = await db.execute(
                select(ChatParticipant).where(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id
                )
            )
            chat_participant = result.scalars().first()
            if not chat_participant:
                print(
                    f"User {user.username} is not a participant in chat {chat_id}")
                await websocket.send_text("Error: You are not a participant in this chat.")
                continue

            # Save message to database
            new_message = ChatMessage(
                chat_id=chat_id, sender_id=user_id, message=message_text)
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)

            # Create response payload
            response = MessageResponse(
                id=new_message.id,
                chat_id=chat_id,
                sender_id=user_id,
                message=message_text,
                created_at=new_message.created_at
            ).model_dump()
            response["created_at"] = response["created_at"].isoformat()

            # Broadcast message to all participants except the sender
            result = await db.execute(
                select(ChatParticipant.user_id).where(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id != user_id  # Exclude the sender
                )
            )
            chat_users = result.scalars().all()

            for chat_user_id in chat_users:
                if chat_user_id in active_connections:
                    await active_connections[chat_user_id].send_text(json.dumps(response))

    except WebSocketDisconnect:
        print(f"User {user.username} disconnected")
        if user_id in active_connections:
            del active_connections[user_id]
