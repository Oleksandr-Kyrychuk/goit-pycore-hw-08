import asyncio
import websockets
import json
from datetime import datetime
from dz5.exchange.currency_service import CurrencyService
from aiofile import async_open
from aiopath import AsyncPath

connected_clients = set()

async def log_exchange_command(command: str, client: str):
    log_file = AsyncPath("exchange_commands.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Client {client} executed: {command}\n"
    async with async_open(log_file, "a") as f:
        await f.write(log_entry)

async def format_rates(rates):
    formatted = []
    for day in rates:
        for date, currencies in day.items():
            formatted.append(f"Дата: {date}")
            for currency, data in currencies.items():
                formatted.append(f"  {currency}: Купівля: {data['purchase']}, Продаж: {data['sale']}")
    return "\n".join(formatted)

async def handle_connection(websocket):
    client = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                command = data.get("command", "").strip()
                if command.startswith("exchange"):
                    parts = command.split()
                    days = 1
                    currencies = ["USD", "EUR"]
                    if len(parts) > 1:
                        try:
                            days = int(parts[1])
                            if not 1 <= days <= 10:
                                await websocket.send(json.dumps({"error": "Днів має бути від 1 до 10"}))
                                continue
                            currencies = parts[2:] if len(parts) > 2 else currencies
                        except ValueError:
                            await websocket.send(json.dumps({"error": "Неправильний формат кількості днів"}))
                            continue
                    await log_exchange_command(command, client)
                    service = CurrencyService(currencies=currencies)
                    rates = await service.get_exchange_rates(days)
                    response = await format_rates(rates)
                    await websocket.send(json.dumps({"message": response}))
                else:
                    # Broadcast regular messages
                    response = {"message": f"{client}: {data.get('message', '')}"}
                    await asyncio.gather(
                        *[client.send(json.dumps(response)) for client in connected_clients]
                    )
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Неправильний формат повідомлення"}))
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

async def main():
    server = await websockets.serve(handle_connection, "localhost", 8765)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())