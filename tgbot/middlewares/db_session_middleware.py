from collections.abc import Awaitable
from typing import Any, Callable, Dict

from aiogram import BaseMiddleware


class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:

        async with self.session_factory() as session:  # <-- создаём сессию
            data["session"] = session

            try:
                result = await handler(event, data)
                await session.commit()  # <-- commit правильно
                return result

            except Exception:
                await session.rollback()  # <-- rollback обязательно await
                raise
