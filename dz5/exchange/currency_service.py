from datetime import datetime, timedelta
from .api_client import PrivatBankAPIClient
from .data_formatter import format_currency_data

class CurrencyService:
    def __init__(self, currencies=None):
        self.client = PrivatBankAPIClient()
        self.currencies = currencies or ["USD", "EUR"]

    async def get_exchange_rates(self, days: int):
        today = datetime.now()
        results = []
        for i in range(days):
            date = today - timedelta(days=i)
            formatted_date = date.strftime("%d.%m.%Y")
            data = await self.client.fetch_rates_for_date(formatted_date)
            filtered = format_currency_data(data, formatted_date, self.currencies)
            results.append(filtered)
        return results
