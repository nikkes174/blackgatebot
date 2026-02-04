from __future__ import annotations

from typing import List, Optional
from sqlalchemy import String, Date, BigInteger, ForeignKey, Integer, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModes(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        unique=True,
        nullable=False
    )
    user_name: Mapped[Optional[str]] = mapped_column(String(255))
    end_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    end_trial_period: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)

    links: Mapped[List["LinkModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class LinkModel(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    link_address: Mapped[str] = mapped_column(String(256), unique=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),  # Ключевой момент
        nullable=True
    )

    user: Mapped[Optional[UserModes]] = relationship(back_populates="links")


class TrialUser(Base):
    __tablename__ = "trial_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_trial_start: Mapped[Optional[Date]] = mapped_column(Date)


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
