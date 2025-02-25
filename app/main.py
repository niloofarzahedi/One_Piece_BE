from fastapi import FastAPI
from app.api.endpoints import users, auth

app = FastAPI()

# Include users API
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}
