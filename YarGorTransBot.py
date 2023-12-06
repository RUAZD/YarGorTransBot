import asyncio

import bot

if __name__ == '__main__':
    try:
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        # При завершении работы скрипта комбинацией клавиш Ctrl + C
        pass
