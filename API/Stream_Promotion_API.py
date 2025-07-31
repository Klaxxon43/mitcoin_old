import aiohttp
import asyncio
from typing import Dict, Any, List, Optional

class StreamPromotionAPI:
    def __init__(self, api_key: str):
        self.api_url = "https://stream-promotion.ru/api/v2"
        self.api_key = api_key
        self.headers = {
            "User-Agent": "StreamPromotionAPI/1.0",
            "Content-Type": "application/json"
        }

    async def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=data,
                headers=self.headers
            ) as response:
                return await response.json()
            
    async def get_services(self) -> List[Dict[str, Any]]:
        """Получить список всех доступных услуг"""
        data = {
            "key": self.api_key,
            "action": "services"
        }
        return await self._make_request(data)
    
    async def get_service(self, service_id: int) -> Dict[str, Any]:
        """Получить конкретную услугу по ID"""
        data = {
            "key": self.api_key,
            "action": "services"
        }
        
        try:
            services = await self._make_request(data)
            if isinstance(services, list):
                for service in services:
                    if str(service.get('service')) == str(service_id):
                        return service
            return None
        except Exception as e:
            print(f"Error getting service {service_id}: {e}")
            return None
    
    async def get_balance(self) -> Dict[str, Any]:
        """Получить текущий баланс аккаунта"""
        data = {
            "key": self.api_key,
            "action": "balance"
        }
        return await self._make_request(data)
    
    async def create_order(
        self,
        service_id: int,
        link: str,
        quantity: int,
        runs: Optional[int] = None,
        interval: Optional[int] = None,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создать новый заказ
        
        :param service_id: ID услуги
        :param link: Ссылка на целевой объект (канал, пост и т.д.)
        :param quantity: Количество (подписчиков, лайков и т.д.)
        :param runs: Количество запусков (опционально)
        :param interval: Интервал между запусками в минутах (опционально)
        :param comments: Кастомные комментарии (опционально)
        
        :return: Словарь с ответом API или None в случае ошибки
        """
        data = {
            "key": self.api_key,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        
        if runs:
            data["runs"] = runs
        if interval:
            data["interval"] = interval
        if comments:
            data["comments"] = comments
            
        try:
            response = await self._make_request(data)
            
            if not response:
                print("Пустой ответ от API при создании заказа")
                return None
                
            if isinstance(response, dict) and 'error' in response:
                print(f"API вернул ошибку: {response['error']}")
                return None
                
            if isinstance(response, dict) and 'order' in response:
                return response
                
            print(f"Неожиданный формат ответа от API: {response}")
            return None
            
        except Exception as e:
            print(f"Ошибка при создании заказа: {str(e)}")
            return None
    
    async def get_order_status(self, order_id: int) -> Dict[str, Any]:
        """
        Получить статус заказа
        
        :param order_id: ID заказа
        """
        data = {
            "key": self.api_key,
            "action": "status",
            "order": order_id
        }
        return await self._make_request(data)

    async def get_multiple_orders_status(self, order_ids: List[int]) -> Dict[str, Any]:
        """
        Получить статус нескольких заказов
        
        :param order_ids: Список ID заказов
        """
        data = {
            "key": self.api_key,
            "action": "status",
            "orders": ",".join(map(str, order_ids))
        }
        return await self._make_request(data)




async def main():
    api = StreamPromotionAPI("MgfYaASx8wwAsASEAmLtytoy2qM1QH84")
    
    # print(await api.get_order_status(4354606))
    # Получаем список услуг
    # services = await api.get_services()
    # print("Список услуг:", services)
    
    
    # # Проверяем баланс
    # balance = await api.get_balance()
    # print("Баланс: " + str(balance['balance'])+ "USD")
    
    # # Создаем заказ (пример для Instagram подписчиков)
    # new_order = await api.create_order(
    #     service_id=5,  # ID услуги из списка
    #     link="https://instagram.com/ваш_аккаунт",
    #     quantity=1000
    # )
    # print("Новый заказ:", new_order)
    
    # # Проверяем статус заказа
    # if new_order.get("status") == "success":
    #     order_id = new_order["order"]
    #     order_status = await api.get_order_status(order_id)
    #     print("Статус заказа:", order_status)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
