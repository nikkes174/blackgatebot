from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from db.models import TrialUser, UserModes


class TrialCrud:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_trial_user(self, user_id: int):
        stmt = select(TrialUser).where(TrialUser.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def add_trial_user(self, user_id: int, username: str):
        trial_user = TrialUser(
            user_id=user_id,
            user_name=username,
            last_trial_start=date.today()
        )

        self.session.add(trial_user)
        await self.session.flush()

        return trial_user