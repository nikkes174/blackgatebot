from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Referral


class ReferralCrud:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_referral(self, user_id: int, referrer_id: int):
        ref = Referral(user_id=user_id, referrer_id=referrer_id)
        self.session.add(ref)
        await self.session.commit()
        return ref

    async def get_referral(self, user_id: int, referrer_id: int):
        result = await self.session.execute(
            select(Referral).where(
                Referral.user_id == user_id,
                Referral.referrer_id == referrer_id
            )
        )
        return result.scalars().first()

    async def increment_ref_count(self, referrer_id: int):
        result = await self.session.execute(
            select(Referral).where(Referral.referrer_id == referrer_id)
        )
        ref = result.scalars().first()

        if ref:
            ref.ref_count = (ref.ref_count or 0) + 1
            await self.session.commit()
            return ref
        return None

    async def get_user_ref_stats(self, user_id: int):
        result = await self.session.execute(
            select(func.count(Referral.id))
            .where(Referral.referrer_id == user_id)
        )
        ref_count = result.scalar() or 0

        if ref_count >= 20:
            discount = 100
        elif ref_count >= 10:
            discount = 25
        elif ref_count >= 5:
            discount = 10
        else:
            discount = 0

        return ref_count, discount

