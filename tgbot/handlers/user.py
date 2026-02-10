import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud_link import LinkService
from db.crud_referral import ReferralCrud
from db.crud_trial import TrialCrud
from db.crud_user import UserCrud
from db.models import UserModes
from new_payment import PaymentUtils
from tgbot.keyboards.inline import (
    first_start_keyboard,
    period_subscriptions,
    to_back,
    to_back_two,
    trail_button,
)
from tgbot.services.broadcaster import safe_broadcast
from utils import MOSCOW_TZ, notify_users_today

user_router = Router()

pay = PaymentUtils()

admin_id = int(os.getenv("ADMIN_ID"))


class BroadcastStates(StatesGroup):
    waiting_for_message = State()


class SendMessageStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message = State()


class SubStates(StatesGroup):
    choosing_device = State()


async def send_main_menu(
    *,
    session: AsyncSession,
    user_id: int,
    username: str,
    message: Message,
):
    user_crud = UserCrud(session)
    ref_crud = ReferralCrud(session)

    user = await user_crud.get_user(user_id)
    if not user:
        user = await user_crud.add_user(
            user_id=user_id,
            user_name=username,
        )

    end_date = user.end_date
    ref_count, discount = await ref_crud.get_user_ref_stats(user_id)

    caption = (
        "🔥 Добро пожаловать в BlackGate 🔥\n\n"
        f"📅 Подписка активна до: <b>{end_date or 'Нет активной подписки'}</b>\n"
        f"👥 Приглашённых: <b>{ref_count}</b>\n"
        f"🎁 Ваша скидка: <b>{discount}%</b>\n"
    )

    video_path = "/usr/src/app/Files/1.mp4"
    video = FSInputFile(video_path)

    await message.answer_video(
        video=video,
        caption=caption,
        reply_markup=first_start_keyboard(),
        parse_mode="HTML",
    )


@user_router.message(F.video)
async def get_file_id(message: Message):
    await message.answer(f"file_id: {message.video.file_id}")


@user_router.message(CommandStart())
async def user_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    args = command.args

    try:
        await message.delete()
    except:
        pass

    user_crud = UserCrud(session)
    ref_crud = ReferralCrud(session)

    user = await user_crud.get_user(user_id)
    if not user:
        user = await user_crud.add_user(
            user_id=user_id,
            user_name=username,
        )

    if args and args.startswith("ref_"):
        referrer_id = int(args.replace("ref_", ""))
        if referrer_id != user_id:
            inviter = await user_crud.get_user(referrer_id)
            if inviter:
                existing = await ref_crud.get_referral(user_id, referrer_id)
                if not existing:
                    await ref_crud.add_referral(user_id, referrer_id)

    await send_main_menu(
        session=session,
        user_id=user_id,
        username=username,
        message=message,
    )


@user_router.callback_query(F.data == "paying_for_subscriptions")
async def subscriptions_handler(call: CallbackQuery):
    await call.answer()

    try:
        await call.message.delete()
    except TelegramBadRequest:
        pass

    await call.message.answer(
        "👇🏾Выберите нужный тариф\n"
        "🔑После оплаты вам придёт ключ для подключения\n"
        "❗️В день окончания подписки вам придёт уведомление\n",
        reply_markup=period_subscriptions(),
    )


@user_router.callback_query(F.data.in_(["one_mouth", "six_mouth"]))
async def handle_subscription(
    callback_query: CallbackQuery, state: FSMContext
):
    await callback_query.answer()

    try:
        await callback_query.message.delete()
    except TelegramBadRequest:
        pass

    if callback_query.data == "one_mouth":
        months = 1
        days = 30
        text = (
            f"🔥Вы выбрали подписку на {months} мес.\n\n"
            "💥Введите количество устройств цифрой:\n"
        )
    else:
        months = 6
        days = 180
        text = (
            f"🔥Вы выбрали подписку на {months} мес.\n\n"
            "💥Введите количество устройств цифрой:\n"
        )

    await state.update_data(months=months, days=days)

    await callback_query.message.answer(text, reply_markup=to_back_two())
    await state.set_state(SubStates.choosing_device)


@user_router.message(SubStates.choosing_device)
async def handle_device_input(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
):
    user_id = message.from_user.id
    username = message.from_user.username or "anonymous"
    raw = (message.text or "").strip()

    if not raw.isdigit():
        await message.answer("❗ Введите количество устройств цифрой.")
        return

    device_count = int(raw)
    if device_count < 1:
        await message.answer("❌ Количество устройств должно быть хотя бы 1.")
        return

    data = await state.get_data()
    months = data.get("months")

    user_crud = UserCrud(session)
    ref_crud = ReferralCrud(session)

    # Создание платежа
    try:
        payment_id, payment_url = await pay.create_payment(
            ref_crud=ref_crud,
            user_id=user_id,
            months=months,
            device_count=device_count,
        )
    except Exception:
        await message.answer("❌ Ошибка при создании платежа.")
        await state.clear()
        return

    # Отправляем ссылку на оплату
    await bot.send_message(
        user_id,
        (
            f"❗️После оплаты в течение минуты вам придёт ключ для подключения❗️\n\n"
            f'<a href="{payment_url}">💰Оплатить💰</a>\n'
        ),
        parse_mode="HTML",
    )

    # Фоновая задача проверки оплаты
    asyncio.create_task(
        pay.check_payment_loop(
            payment_id=payment_id,
            user_id=user_id,
            username=username,
            months=months,
            device_count=device_count,
            bot=bot,
        )
    )

    await state.clear()


@user_router.callback_query(F.data == "test_period")
async def paying_for_subscriptions_handler(call: CallbackQuery):
    await call.answer()

    try:
        await call.message.delete()
    except TelegramBadRequest:
        pass

    await call.message.answer(
        "👇Нажмите кнопку ниже для получения пробного периода\n",
        reply_markup=trail_button(),
        parse_mode="HTML",
    )


@user_router.callback_query(F.data == "active_test")
async def get_test_link(call: CallbackQuery, bot: Bot, session: AsyncSession):
    await call.answer()

    user_id = call.from_user.id
    username = call.from_user.username or "unknown"

    link_service = LinkService(session)
    trial_crud = TrialCrud(session)

    today = datetime.now(MOSCOW_TZ).date()
    trial_end = today + timedelta(days=3)

    user = await session.scalar(
        select(UserModes).where(UserModes.user_id == user_id)
    )

    if not user:
        user = UserModes(user_id=user_id, user_name=username)
        session.add(user)
        await session.flush()

    trial_user = await trial_crud.get_trial_user(user_id)
    if trial_user:
        await call.message.answer(
            "❌ Вы уже активировали пробный период.", reply_markup=to_back()
        )
        return

    free_links = await link_service.get_free_random_links(1)
    if not free_links:
        await call.message.answer("❌ Нет свободных ссылок.")
        return

    link_obj = free_links[0]

    link_obj.user_id = user.user_id
    await session.flush()

    await trial_crud.add_trial_user(user.user_id, username)

    user.end_trial_period = trial_end

    await session.commit()

    await call.message.answer(
        "🎉 Пробная подписка активирована!\n\n"
        "Ваш ключ (нажмите для копирования):\n\n"
        f"<code>{link_obj.link_address}</code>\n\n"
        "📘 Инструкция по установке и подключению:\n"
        '<a href="https://telegra.ph/Instrukciya-po-podklyucheniyu-07-14">Открыть инструкцию</a>',
        parse_mode="HTML",
        reply_markup=to_back_two(),
    )

    try:
        await bot.send_message(
            admin_id,
            "🧪 Активирован пробный период!\n\n"
            f"👤 Пользователь: {user_id} (@{username})\n"
            f"📅 Действует до: {trial_end}\n\n"
            f"🔑 Выданный ключ:\n<code>{link_obj.link_address}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        print("[TRIAL ADMIN NOTIFY ERROR]:", e)




@user_router.callback_query(F.data == "our_reff_link")
async def get_reff_link(call: CallbackQuery, session: AsyncSession, bot: Bot):
    await call.answer()

    user_id = call.from_user.id
    user_crud = UserCrud(session)

    user = await user_crud.get_user(user_id)

    if user:
        ref_link = f"https://t.me/BlackGateGuard_bot?start=ref_{user_id}"
        await bot.send_message(
            user_id,
            f"🔗 Ваша реферальная ссылка:\n{ref_link}\n",
            parse_mode="HTML",
        )
    else:
        await bot.send_message(
            user_id,
            "⚠️ Реферальная ссылка доступна только при активной подписке.",
        )


@user_router.callback_query(F.data == "send_all")
async def send_all(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if call.from_user.id != admin_id:
        await call.message.answer("Нет доступа.")
        return

    await call.message.answer("Введите сообщение для рассылки:")
    await state.set_state(BroadcastStates.waiting_for_message)



from db.crud_user import UserCrud

@user_router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(
    message: Message,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
):
    text = message.text
    user_crud = UserCrud(session)

    users = await user_crud.get_all_users()

    stats = await safe_broadcast(
        bot=bot,
        users=users,
        text=text,
    )

    await message.answer(
        "📨 <b>Рассылка завершена</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total']}</b>\n"
        f"✅ Отправлено: <b>{stats['sent']}</b>\n"
        f"🚫 Заблокировали бота: <b>{stats['blocked']}</b>\n"
        f"⚠️ Ошибки: <b>{stats['failed']}</b>",
        parse_mode="HTML",
    )

    await state.clear()


@user_router.callback_query(F.data == "send_user")
async def send_message_to_user_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()

    await call.message.answer("Введите ID пользователя:")
    await state.set_state(SendMessageStates.waiting_for_user_id)


@user_router.message(SendMessageStates.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer("❗ Введите корректный ID")
        return

    await state.update_data(user_id=raw)
    await message.answer("Теперь введите текст сообщения:")
    await state.set_state(SendMessageStates.waiting_for_message)


@user_router.message(SendMessageStates.waiting_for_message)
async def process_message_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = int(data["user_id"])
    text = message.text

    try:
        await bot.send_message(user_id, text)
        await message.answer("Отправлено!")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

    await state.clear()


@user_router.callback_query(F.data == "back_to_menu")
async def back_to_menu(
    call: CallbackQuery,
    session: AsyncSession,
):
    await call.answer()

    user_id = call.from_user.id
    username = call.from_user.username or ""

    await send_main_menu(
        session=session,
        user_id=user_id,
        username=username,
        message=call.message,
    )


@user_router.callback_query(F.data == "to_chek")
async def admin_check_subscriptions(
    call: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
):
    if call.from_user.id != admin_id:
        await call.answer("Нет доступа", show_alert=True)
        return

    await call.answer("⏳ Запускаю проверку...")

    count = await notify_users_today(
        session=session,
        bot=bot,
    )

    await call.message.answer(
        f"✅ Проверка завершена\n"
        f"📨 Уведомлено пользователей: <b>{count}</b>",
        parse_mode="HTML",
    )
