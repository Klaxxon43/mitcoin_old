from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Импортируйте ваш бот и базу данных
from datebase.db import DB
app = FastAPI()

# Модель для запроса
class UserRequest(BaseModel):
    user_id: int

# Эндпоинт для получения баланса пользователя
@app.post("/get_balance")
async def get_balance(request: UserRequest):
    user_id = request.user_id
    balance = await DB.get_user_balance(user_id)  # Замените на ваш метод для получения баланса

    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": user_id, "balance": balance}

@app.post("/get_user")
async def get_balance(request: UserRequest):
    user_id = request.user_id
    res = await DB.select_user(user_id)  # Замените на ваш метод для получения баланса

    if res is None:
        raise HTTPException(status_code=404, detail="User not found")

    return res

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


