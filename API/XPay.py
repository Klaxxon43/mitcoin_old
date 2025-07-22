import httpx
import asyncio
import uuid
from typing import Optional, Dict, List, Tuple
from utils.Imports import *

SHOP_ID = 458
TOKEN = 'x-bb3735531298eb51ba8f2308f7a4eec6'


class XPayClient:
    def __init__(self, base_url: str = "https://xpay.bot-wizard.org:5000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(verify=False)

    async def create_invoice(
        self,
        amount: float,
        description: str,
        payload: Optional[str] = None,
        shop_id: int = SHOP_ID,
        token: str = TOKEN,
        user_id: Optional[int] = None
    ) -> Dict[str, str]:
        
        url = f"{self.base_url}/shop{shop_id}/{token}/createInvoice"
        data = {"amount": amount, "description": description, "payload": payload}
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        res = response.json()
        
        unique_id = res['url'].split('startapp=')[1]

        # Сохраняем в БД
        if user_id is not None:
            await DB.add_deposit(
                user_id=user_id,
                amount=int(amount), 
                unique_id=unique_id,
                status="pending",
                service="xpay",
                item=description
            )

        return {
            'url': res['url'],
            'unique_id': unique_id
        }


    async def get_updates(self, shop_id: int = SHOP_ID, token: str = TOKEN) -> List[Dict]:
        url = f"{self.base_url}/shop{shop_id}/{token}/getUpdates"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def check_payment_status(self, unique_id: str):
        updates = await self.get_updates()
        updated = False

        for payment in updates:
            if payment['unique_id'] == unique_id:
                await DB.update_deposit(unique_id, status="paid")
                updated = True
            else:
                # Даже если кто-то другой оплатил, его тоже нужно обновить:
                await DB.update_deposit(payment['unique_id'], status="paid")

        return updated


    async def close(self):
        await self.client.aclose()

