import asyncio
import logging
import os

import betterlogging as bl
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    MenuButtonCommands,
)
from dotenv import load_dotenv

from db.db import AsyncSessionLocal
from tgbot.config import Config, load_config
from tgbot.handlers import user_router
from tgbot.handlers.admin import admin_router
from tgbot.middlewares.config import ConfigMiddleware
from tgbot.middlewares.db_session_middleware import DBSessionMiddleware
from tgbot.services import broadcaster
from utils import Scheduler

load_dotenv()


async def on_startup(bot: Bot, admin_ids: list[int]):
    commands = [
        BotCommand(command="start", description="Перезапуск бота"),
        BotCommand(command="admin_panel", description="Панель админа"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    await broadcaster.broadcast(bot, admin_ids, "Бот запущен")


def register_global_middlewares(dp: Dispatcher, config: Config):
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.callback_query.outer_middleware(ConfigMiddleware(config))

    dp.message.outer_middleware(DBSessionMiddleware(AsyncSessionLocal))
    dp.callback_query.outer_middleware(DBSessionMiddleware(AsyncSessionLocal))


def setup_logging():
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
        "[%(asctime)s] - %(name)s - %(message)s",
    )
    logging.getLogger(__name__).info("Starting bot")


def get_storage(config: Config):
    if config.tg_bot.use_redis:
        return RedisStorage.from_url(
            config.redis.dsn(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    return MemoryStorage()


async def main():
    setup_logging()
    config = load_config(".env")
    storage = get_storage(config)

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher(storage=storage)

    register_global_middlewares(dp, config)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    ADMIN_ID = int(os.getenv("ADMIN_ID"))

    scheduler = Scheduler(AsyncSessionLocal)
    asyncio.create_task(scheduler.run_daily_admin_report(bot, ADMIN_ID))

    await on_startup(bot, [ADMIN_ID])

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот остановлен!")
