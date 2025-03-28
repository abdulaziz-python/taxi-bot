import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.setup import create_tables
from handlers import register_all_handlers

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
    dp = Dispatcher(storage=MemoryStorage())
    
    register_all_handlers(dp)
    
    await create_tables()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())