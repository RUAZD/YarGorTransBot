import asyncio
from dataclasses import dataclass


@dataclass
class User:
    telegram_id: int
    routes_favorite: list[str] = None
    routes_history: list[str] = None
    stations_favorite: list[str] = None
    stations_history: list[str] = None

    def __post_init__(self):
        self.routes_favorite = self.routes_favorite if self.routes_favorite is not None else list()
        self.routes_history = self.routes_history if self.routes_history is not None else list()
        self.stations_favorite = self.stations_favorite if self.stations_favorite is not None else list()
        self.stations_history = self.stations_history if self.stations_history is not None else list()


import aiosqlite
async def create_table():
    async with aiosqlite.connect('weather.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS requests '
                         '(date text, city text, weather text)')
        await db.commit()
async def save_to_db(city, weather):
    async with aiosqlite.connect('weather.db') as db:
        await db.execute('INSERT INTO requests VALUES (?, ?, ?)',
                         (datetime.now(), city, weather))
        await db.commit()


async def main():
    await create_table()
    app = web.Application()
    app.add_routes([web.get('/weather', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()


if __name__ == '__main__':
    asyncio.run(main())
