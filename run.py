import aiohttp
import asyncio
import json
from datetime import datetime, timedelta


class ExchangeRates:
    BASE_URL = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5&date="
    CURRENCY_CODES = ["USD", "EUR"]
    DATE_RANGE = 10

    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def fetch(self, url):
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"Error fetching {url}: status code {response.status}")
            return await response.text()

    async def get_rates(self):
        today = datetime.now()
        date_range = [today - timedelta(days=x) for x in range(self.DATE_RANGE)]
        for date in date_range:
            url = f'{self.BASE_URL}{date.strftime("%d.%m.%Y")}'
            response_text = await self.fetch(url)
            response_json = json.loads(response_text)
            for currency in response_json:
                if currency["ccy"] in self.CURRENCY_CODES:
                    print(
                        f'{date:%d.%m.%Y},Курс {currency["ccy"]}:\n Продаж {currency["sale"]} Купівля {currency["buy"]}'
                    )

    async def close(self):
        await self.session.close()


async def main():
    exchange_rates = ExchangeRates()
    try:
        await exchange_rates.get_rates()
    finally:
        await exchange_rates.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
