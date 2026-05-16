from fastapi import FastAPI
from app.routers import health

app = FastAPI(title="SYNC Backend API")

app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "Welcome to SYNC API"}
