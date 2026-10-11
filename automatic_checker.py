import asyncio

from main import run_api_check
from apisTable import get_due_apis
import sqlite3

conn = sqlite3.connect("database.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()



async def main():

    while True:

        apis = get_due_apis(c)

        for api in apis:
            try:
                await run_api_check(c,api[0],conn)

            except Exception as e:
                print(f"Failed checking API {api[0]}: {e}")

        await asyncio.sleep(60)


asyncio.run(main())