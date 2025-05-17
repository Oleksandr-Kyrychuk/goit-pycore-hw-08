import asyncio
import sys
from exchange.currency_service import CurrencyService

async def main():
    try:
        if len(sys.argv) < 2:
            raise ValueError("Потрібно вказати кількість днів.")
        days = int(sys.argv[1])
        if not 1 <= days <= 10:
            raise ValueError("Число днів має бути в межах від 1 до 10.")
        # Get currencies from arguments (default to USD, EUR if none provided)
        currencies = sys.argv[2:] if len(sys.argv) > 2 else ["USD", "EUR"]
        if not currencies:
            raise ValueError("Потрібно вказати хоча б одну валюту.")
    except ValueError as e:
        print(f"Використання: python main.py <1-10> [валюта1] [валюта2] ...")
        print(f"Помилка: {e}")
        return

    service = CurrencyService(currencies=currencies)
    result = await service.get_exchange_rates(days)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())