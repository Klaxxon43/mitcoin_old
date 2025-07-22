# # main.py
# from fastapi import FastAPI
# from pydantic import BaseModel

# app = FastAPI()

# class PaymentData(BaseModel):
#     payment_id: str
#     order_id: str
#     amount: int
#     currency: str
#     method: str

# @app.post("/api/payment-success")
# async def handle_payment(data: PaymentData):
#     return {"status": "received", "data": data.dict()}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=5000)
print(len('🔥'))