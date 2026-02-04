from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LinkModel


class LinkService:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_link_random_kink(self):
        stmt = (
            select(LinkModel)
            .where(LinkModel.user_id.is_(None))
            .order_by(func.random())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_free_random_links(self, count: int):
        stmt = (
            select(LinkModel)
            .where(LinkModel.user_id.is_(None))
            .order_by(func.random())
            .limit(count)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def assign_one_link_to_user(self, user_id: int):
        link = await self.get_free_random_links(1)
        if not link:
            return None

        link = link[0]
        link.user_id = user_id

        await self.session.commit()
        await self.session.refresh(link)

        return link

    async def assign_links_to_user(self, user_id: int, count: int):
        links = await self.get_free_random_links(count)

        if len(links) < count:

            return None

        for link in links:
            link.user_id = user_id

        await self.session.commit()




        for link in links:
            await self.session.refresh(link)

        return links

    async def get_user_links(self, user_id: int):
        stmt = select(LinkModel).where(LinkModel.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalars().all()