import asyncio
import json
from datetime import datetime, timedelta
import aiohttp
import names
import logging
import aiofile
import aiopath
import websockets
from websockets.exceptions import ConnectionClosedOK
from websockets import WebSocketServerProtocol


logging.basicConfig(level=logging.INFO)


class ExchangeRates:
    BASE_URL = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5&date="
    DATE_RANGE = 10

    def __init__(self, currency_codes):
        self.currency_codes = currency_codes
        self.session = None

    async def create_session(self):
        self.session = aiohttp.ClientSession()

    async def fetch(self, url):
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"Error fetching {url}: status code {response.status}")
            return await response.text()

    async def get_rates(self, days=1):
        today = datetime.now()
        date_range = [today - timedelta(days=x) for x in range(days)]
        result = ''
        for date in date_range:
            url = f'{self.BASE_URL}{date.strftime("%d.%m.%Y")}'
            response_text = await self.fetch(url)
            response_json = json.loads(response_text)
            for currency in response_json:
                if currency["ccy"] in self.currency_codes:
                    result += (
                        '{date:%d.%m.%Y}, Курс {currency["ccy"]}:\nПродаж {currency["sale"]}, Купівля {currency["buy"]}\n'
                    )
        return result

    async def close(self):
        await self.session.close()


class Server:
    clients = set()
    currency_codes = ["USD", "EUR"]  # валюти за замовчуванням
    exchange_rates = ExchangeRates(currency_codes)

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.lower().startswith('exchange'):
                try:
                    days = int(message.split()[1])
                except:
                    days = 1
                result = await self.exchange_rates.get_rates(days)
                await self.send_to_clients(result)

                async with aiofile.async_open(aiopath.Path(__file__).parent / 'chat.log', mode='a') as f:
                    await f.write(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}:\n{result}\n')
            elif message == 'Hi Server':
                await self.send_to_clients(f"{ws.name}: {message}")
                await self.send_to_clients('Привіт мої любі!')
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    await server.exchange_rates.create_session()  # initialize session
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
