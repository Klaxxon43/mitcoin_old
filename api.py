from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
import logging
import traceback
from utils.Imports import *
import asyncio
from typing import Optional

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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await DB.create()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    yield  # Всё готово
    # (можно добавить shutdown-логику после yield)

app = FastAPI(lifespan=lifespan)


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

class MiningStatusResponse(BaseModel):
    is_active: bool
    time_left: Optional[str] = None
    earnings: Optional[float] = None

class MiningStartRequest(BaseModel):
    user_id: int
    deposit: int = 1

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
import logging
import traceback
from utils.Imports import *
import asyncio
from typing import Optional
from datetime import datetime

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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await DB.create()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    yield
    # (можно добавить shutdown-логику после yield)

app = FastAPI(lifespan=lifespan)

# Константы майнинга
MINING_RATE_PER_HOUR = 1000  # 1000 монет в час
MAX_MINING_HOURS = 2         # Максимум 2 часа майнинга
MIN_MINIG_TIME_MINUTES = 5   # Минимальное время для сбора (5 минут)

@app.post("/get_balance")
async def get_balance(request: UserRequest):
    try:
        user_id = request.user_id
        logger.info(f"Requesting balance for user {user_id}")
        
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

class MiningStatusResponse(BaseModel):
    is_active: bool
    time_left: Optional[str] = None
    earnings: Optional[float] = None
    mined_time: Optional[str] = None
    can_collect: Optional[bool] = None
    deposit: Optional[int] = None

class MiningStartRequest(BaseModel):
    user_id: int
    deposit: int = 1

@app.post("/mining/start")
async def start_mining(request: MiningStartRequest):
    """Активирует майнинг для пользователя"""
    try:
        # Проверяем, есть ли уже активный майнинг
        mining_data = await DB.search_mining(request.user_id)
        if mining_data:
            raise HTTPException(status_code=400, detail="Mining already active")
        
        # Активируем майнинг
        success = await DB.add_mining(request.user_id, request.deposit)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start mining")
        
        return {"status": "success", "message": "Mining started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting mining: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/mining/stop")
async def stop_mining(request: UserRequest):
    """Останавливает майнинг для пользователя"""
    try:
        mining_data = await DB.search_mining(request.user_id)
        if not mining_data:
            raise HTTPException(status_code=404, detail="No active mining found")
        
        success = await DB.remove_mining(request.user_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop mining")
        
        return {"status": "success", "message": "Mining stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping mining: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/mining/status")
async def mining_status(request: UserRequest):
    """Проверяет статус майнинга"""
    try:
        user_id = request.user_id
        mining_data = await DB.search_mining(user_id)
        
        if not mining_data:
            return MiningStatusResponse(is_active=False)
        
        # Получаем данные о депозите
        deposit_data = await DB.get_deposit_mining(user_id)
        deposit = deposit_data[0][0] if deposit_data else 1
        
        # Получаем время последнего сбора
        time_str = await DB.get_last_collection_time(user_id)
        last_collection_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        
        # Рассчитываем прошедшее время
        current_time = datetime.now()
        time_diff = current_time - last_collection_time
        total_seconds = time_diff.total_seconds()
        total_minutes = total_seconds / 60
        total_hours = total_seconds / 3600
        
        # Форматируем время для отображения
        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        time_parts = []
        if days > 0:
            time_parts.append(f"{days}д")
        if hours > 0:
            time_parts.append(f"{hours}ч")
        if minutes > 0 or (days == 0 and hours == 0):
            time_parts.append(f"{minutes}м")
        
        mined_time_str = " ".join(time_parts)
        
        # Рассчитываем доступные для сбора средства
        effective_mining_hours = min(total_hours, MAX_MINING_HOURS)
        mined_amount = effective_mining_hours * MINING_RATE_PER_HOUR * deposit
        
        # Проверяем, можно ли уже собрать
        can_collect = total_minutes >= MIN_MINIG_TIME_MINUTES
        
        # Рассчитываем оставшееся время до максимальной награды
        if total_hours < MAX_MINING_HOURS:
            remaining_hours = MAX_MINING_HOURS - total_hours
            time_left = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}м"
        else:
            time_left = "Максимум"
        
        return MiningStatusResponse(
            is_active=True,
            time_left=time_left,
            earnings=mined_amount,
            mined_time=mined_time_str,
            can_collect=can_collect,
            deposit=deposit
        )
        
    except Exception as e:
        logger.error(f"Error checking mining status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/mining/collect")
async def collect_mining(request: UserRequest):
    """Собирает награду за майнинг"""
    try:
        user_id = request.user_id
        mining_data = await DB.search_mining(user_id)
        if not mining_data:
            raise HTTPException(status_code=404, detail="No active mining found")
        
        # Получаем данные о депозите
        deposit_data = await DB.get_deposit_mining(user_id)
        deposit = deposit_data[0][0] if deposit_data else 1
        
        # Получаем время последнего сбора
        time_str = await DB.get_last_collection_time(user_id)
        last_collection_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        
        # Рассчитываем прошедшее время
        current_time = datetime.now()
        time_diff = current_time - last_collection_time
        total_seconds = time_diff.total_seconds()
        total_minutes = total_seconds / 60
        total_hours = total_seconds / 3600
        
        # Проверяем минимальное время
        if total_minutes < MIN_MINIG_TIME_MINUTES:
            remaining_seconds = MIN_MINIG_TIME_MINUTES * 60 - total_seconds
            remaining_minutes = int(remaining_seconds // 60)
            remaining_seconds = int(remaining_seconds % 60)
            
            raise HTTPException(
                status_code=400,
                detail=f"Для сбора нужно майнить хотя бы {MIN_MINIG_TIME_MINUTES} минут. Осталось: {remaining_minutes} мин {remaining_seconds} сек"
            )
        
        # Рассчитываем доступные для сбора средства
        effective_mining_hours = min(total_hours, MAX_MINING_HOURS)
        mined_amount = effective_mining_hours * MINING_RATE_PER_HOUR * deposit
        
        # Начисляем баланс
        await DB.add_balance(user_id, mined_amount)
        
        # Обновляем время майнинга
        await DB.update_last_collection_time(user_id, current_time)
        
        # Обновляем статистику
        await DB.add_mined_from_all_stats(user_id, mined_amount)
        
        return {
            "status": "success", 
            "amount": mined_amount,
            "message": f"Successfully collected {mined_amount:.2f} coins"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting mining: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/mining/stats")
async def mining_stats():
    """Получает общую статистику по майнингу"""
    try:
        total_miners = await DB.get_mining_line()
        return {
            "total_miners": total_miners,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting mining stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)