from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
import logging
import traceback
from datebase.db import DB  # Используем ваш существующий класс DB
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI()

# Добавляем CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    user_id: int

@app.on_event("startup")
async def startup_event():
    """Инициализация подключения к БД при старте"""
    try:
        await DB.create()  # Используем ваш существующий метод create()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

@app.post("/get_balance")
async def get_balance(request: UserRequest):
    try:
        user_id = request.user_id
        logger.info(f"Requesting balance for user {user_id}")
        
        # Получаем баланс из вашего существующего метода
        balance = await DB.get_user_balance(user_id)
        
        if balance is None:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"user_id": user_id, "balance": balance}
        
    except Exception as e:
        logger.error(f"Error in get_balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/get_user")
async def get_user(request: UserRequest):
    try:
        user_id = request.user_id
        logger.info(f"Requesting data for user {user_id}")
        
        # Получаем данные пользователя из вашего существующего метода
        user_data = await DB.select_user(user_id)
        
        if user_data is None:
            raise HTTPException(status_code=404, detail="User not found")
            
        return user_data
        
    except Exception as e:
        logger.error(f"Error in get_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/ping")
async def ping():
    return {"status": "alive", "db_connection": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Запускаем в том же event loop, что и aiogram
    loop = asyncio.get_event_loop()
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop=loop)
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())