import asyncio

from aiogram import Bot, Dispatcher

import config

bot = Bot(config.BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler()
async def __(message):
    print(message)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
