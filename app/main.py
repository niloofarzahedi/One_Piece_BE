from fastapi import FastAPI
from app.api.endpoints import users

app = FastAPI()

# Include users API
app.include_router(users.router, prefix="/users", tags=["Users"])


@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}
