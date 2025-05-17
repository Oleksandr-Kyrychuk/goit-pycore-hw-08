import aiohttp
from .exceptions import APIClientError

class PrivatBankAPIClient:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"

    async def fetch_rates_for_date(self, date: str):
        url = self.BASE_URL.format(date=date)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        raise APIClientError(f"Помилка API: {response.status}")
                    return await response.json()
        except Exception as e:
            raise APIClientError(f"Не вдалося отримати дані: {e}")
