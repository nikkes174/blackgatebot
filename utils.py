import asyncio
from datetime import datetime, timedelta
import pytz
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.crud_user import UserCrud
from tgbot.keyboards.inline import period_subscriptions

MOSCOW_TZ = pytz.timezone("Europe/Moscow")


import asyncio
from datetime import datetime, timedelta
import pytz
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.crud_user import UserCrud

MOSCOW_TZ = pytz.timezone("Europe/Moscow")


class Scheduler:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @staticmethod
    async def sleep_until(hour: int, minute: int = 0):
        now = datetime.now(MOSCOW_TZ)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

    async def check_yesterday_expired(self, bot: Bot, admin_id: int):
        async with self.session_maker() as session:
            yesterday = datetime.now(MOSCOW_TZ).date() - timedelta(days=1)
            res = await session.execute(UserCrud.model_select_all())
            users = res.scalars().all()

            expired_paid = []
            expired_trial = []

            for user in users:
                if user.end_date == yesterday:
                    expired_paid.append(
                        f"- {user.user_id} ({user.user_name}) — до {user.end_date}"
                    )

                if user.end_trial_period == yesterday:
                    expired_trial.append(
                        f"- {user.user_id} ({user.user_name}) — триал"
                    )

            if not expired_paid and not expired_trial:
                return

            text = "📆 Отчёт по истёкшим подпискам за вчера:\n\n"

            if expired_paid:
                text += "💳 Оплаченные:\n" + "\n".join(expired_paid) + "\n\n"

            if expired_trial:
                text += "🧪 Триальные:\n" + "\n".join(expired_trial)

            await bot.send_message(admin_id, text)

    async def run_daily_admin_report(self, bot: Bot, admin_id: int):
        while True:
            await self.sleep_until(6, 0)
            await self.check_yesterday_expired(bot, admin_id)





from aiogram.exceptions import TelegramForbiddenError

async def notify_users_today(
    *,
    session: AsyncSession,
    bot: Bot,
) -> int:
    today = datetime.now(MOSCOW_TZ).date()

    res = await session.execute(UserCrud.model_select_all())
    users = res.scalars().all()

    notified = 0

    for user in users:
        try:
            end_d = user.end_date
            end_t = user.end_trial_period

            if end_d:
                if end_d == today:
                    await bot.send_message(
                        user.user_id,
                        "⚠️ Сегодня последний день вашей подписки.\n"
                        "Чтобы продолжить пользоваться сервисом — оформите продление.",
                        reply_markup=period_subscriptions(),
                    )
                    notified += 1

                elif end_d < today:
                    await bot.send_message(
                        user.user_id,
                        "❌ Ваша подписка закончилась.\n"
                        "Чтобы восстановить доступ — оформите подписку.",
                        reply_markup=period_subscriptions(),
                    )
                    notified += 1

            elif end_t:
                if end_t == today:
                    await bot.send_message(
                        user.user_id,
                        "⚠️ Сегодня последний день пробного периода.\n"
                        "Чтобы продолжить пользоваться сервисом — оформите подписку.",
                        reply_markup=period_subscriptions(),
                    )
                    notified += 1

                elif end_t < today:
                    await bot.send_message(
                        user.user_id,
                        "❌ Пробный период завершён.\n"
                        "Чтобы продолжить пользоваться сервисом — оформите подписку.",
                        reply_markup=period_subscriptions(),
                    )
                    notified += 1

        except TelegramForbiddenError:
            # пользователь заблокировал бота — просто пропускаем
            continue

        except Exception as e:
            print(f"[NOTIFY ERROR] user={user.user_id}: {e}")

    return notified
