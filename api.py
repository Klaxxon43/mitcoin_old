from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils.Imports import Bot

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



# --- Модель запроса от сайта ---
class PaymentData(BaseModel):
    payment_id: str
    order_id: str
    amount: int
    currency: str
    method: str

@app.post("/api/payment-success")
async def handle_payment_success(data: PaymentData, bot: Bot):
    # Здесь логика обработки и запись в БД
    text = (
        f"💳 Платёж прошёл успешно!\n\n"
        f"🧾 Order ID: {data.order_id}\n"
        f"💰 Сумма: {data.amount / 100:.2f} {data.currency}\n"
        f"📎 Метод: {data.method}\n"
        f"🆔 ID платежа: {data.payment_id}"
    )

    # Пример отправки администратору
    admin_id = 5129878568
    try:
        await bot.send_message(admin_id, text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send message")

    return {"status": "ok"}


# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

