import asyncio
from aiogram.types import BotCommand
import db
import scheduler
from loader import bot, dp
from handlers import (
    start, oars, menu, diary, tests, library, settings, voice
)

dp.include_router(start.router)
dp.include_router(oars.router)
dp.include_router(menu.router)
dp.include_router(diary.router)
dp.include_router(tests.router)
dp.include_router(library.router)
dp.include_router(settings.router)
dp.include_router(voice.router)


async def main():
    db.init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать сначала"),
        BotCommand(command="menu", description="Главное меню"),
    ])
    asyncio.create_task(scheduler.scheduled_task(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
