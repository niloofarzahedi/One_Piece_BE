from fastapi import FastAPI
from app.api.endpoints import users, auth, chat

app = FastAPI()

# Include users API
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}
