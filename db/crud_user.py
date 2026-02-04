from datetime import date, datetime, timedelta
from typing import Optional

import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserModes


class UserCrud:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(
        self,
        user_id: int,
        user_name: str,
        end_date: Optional[date] = None,
        end_trial_period: Optional[date] = None,
    ):
        user = UserModes(
            user_id=user_id,
            user_name=user_name,
            end_date=end_date,
            end_trial_period=end_trial_period,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user(self, user_id: int):
        result = await self.session.execute(
            select(UserModes).where(UserModes.user_id == user_id)
        )
        return result.scalars().first()

    async def update_date(self, user_id: int, month: int):
        user = await self.get_user(user_id)

        user.end_date = datetime.now(
            pytz.timezone("Europe/Moscow")
        ).date() + relativedelta(months=month)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def update_trial(self, user_id: int):
        user = await self.get_user(user_id)

        user.end_date = datetime.now(
            pytz.timezone("Europe/Moscow")
        ).date() + timedelta(days=3)

        await self.session.commit()
        await self.session.refresh(user)

    async def get_end_date(self, user_id: int):
        stmt = select(UserModes.end_date).where(UserModes.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar()

    @staticmethod
    def model_select_all():
        return select(UserModes)
