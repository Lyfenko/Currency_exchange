import aiohttp
import asyncio
import sys
import json
from datetime import datetime, timedelta


class ExchangeRates:
    BASE_URL = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5&date="
    DATE_RANGE = 10

    def __init__(self, currency_codes):
        self.currency_codes = currency_codes
        self.session = aiohttp.ClientSession()

    async def fetch(self, url):
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"Error fetching {url}: status code {response.status}")
            return await response.text()

    async def get_rates(self, days=10):
        if days > self.DATE_RANGE:
            raise ValueError(f"Error: The number of days cannot exceed {self.DATE_RANGE}")
        today = datetime.now()
        date_range = [today - timedelta(days=x) for x in range(days)]
        for date in date_range:
            url = f'{self.BASE_URL}{date.strftime("%d.%m.%Y")}'
            response_text = await self.fetch(url)
            response_json = json.loads(response_text)
            for currency in response_json:
                if currency["ccy"] in self.currency_codes:
                    print(
                        f'{date:%d.%m.%Y},Курс {currency["ccy"]}:\n Продаж {currency["sale"]} Купівля {currency["buy"]}'
                    )

    async def close(self):
        await self.session.close()


async def main():
    currency_codes = ["USD", "EUR"]  # валюти за замовчуванням
    if len(sys.argv) > 1:
        currency_codes = sys.argv[1:]
    exchange_rates = ExchangeRates(currency_codes)
    try:
        days = int(input("Введіть кількість днів для виводу курсу валют: "))
        await exchange_rates.get_rates(days)
        print("Введіть команду exit, щоб вийти з програми.")
        while True:
            user_input = input()
            if user_input.lower() == "exit":
                break
            else:
                print("Невідома команда. Доступна тільки команда exit.")
    except ValueError as e:
        print(e)
    finally:
        await exchange_rates.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
