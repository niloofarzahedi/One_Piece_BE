from fastapi import APIRouter, WebSocket, Depends, WebSocketException, status
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.core.security import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from app.db.session import get_db
from app.db.models.user import User


router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db), username: str = Depends(get_current_user)):
    """Restrict WebSocket access to authenticated users."""
    try:
        if username is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        user = db.query(User).filter(User.username == username).first()
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
