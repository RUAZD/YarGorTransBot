import asyncio
import sys

import bot

if __name__ == '__main__':
    try:
        asyncio.run(bot.main(sys.argv))
    except KeyboardInterrupt:
        # При завершении работы программы в PyCharm
        pass
