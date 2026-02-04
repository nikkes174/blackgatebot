import asyncio
import os

from dotenv import load_dotenv
from yookassa import Configuration, Payment

from db.crud_link import LinkService
from db.crud_referral import ReferralCrud
from db.crud_user import UserCrud
from db.db import AsyncSessionLocal

load_dotenv()


class PaymentUtils:

    def __init__(self):
        self.yookassa_id = os.getenv("YOOKASSA_SHOP_ID")
        self.yookassa_key = os.getenv("YOOKASSA_SECRET_KEY")

        Configuration.account_id = self.yookassa_id
        Configuration.secret_key = self.yookassa_key

        self.active_payment_users = set()

    # ---------------------------------------------------------
    # Проверка статуса платежа (СИНХРОННАЯ функция YooKassa)
    # ---------------------------------------------------------
    def check_payment_status(self, payment_id: str):
        try:
            payment = Payment.find_one(payment_id)
            return payment.status, payment.metadata
        except Exception:
            return None, None

    async def create_payment_async(self, payload: dict):
        return await asyncio.to_thread(Payment.create, payload)

    # ---------------------------------------------------------
    # Получить скидку по количеству рефералов
    # ---------------------------------------------------------
    async def get_discount_by_ref_count(self, ref_crud: ReferralCrud, user_id: int) -> int:
        ref_count, _ = await ref_crud.get_user_ref_stats(user_id)

        if ref_count >= 20:
            return 100
        if ref_count >= 10:
            return 25
        if ref_count >= 5:
            return 10
        return 0

    # ---------------------------------------------------------
    # Создание платежа
    # ---------------------------------------------------------
    async def create_payment(self, ref_crud: ReferralCrud, user_id: int, months: int, device_count: int):
        return_url = "https://t.me/BlackGateGuard_bot"

        # ---- НОВАЯ ТАРИФНАЯ ЛОГИКА ----
        if months == 1:
            # 1 месяц
            if device_count == 1:
                base_price = 120
            else:
                base_price = 100 * device_count

        elif months == 6:
            # 6 месяцев
            if device_count == 1:
                base_price = 500
            else:
                base_price = 80 * 6 * device_count

        else:
            raise ValueError(f"Неизвестный срок подписки: {months}")
        # --------------------------------

        discount = await self.get_discount_by_ref_count(ref_crud, user_id)

        amount = base_price * (100 - discount) / 100
        if amount <= 0:
            raise RuntimeError("Сумма платежа равна 0 — YooKassa не принимает такие платежи.")

        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": f"Подписка на {months} мес. | устройств: {device_count} | скидка: {discount}% | user={user_id}",
            "metadata": {
                "user_id": str(user_id),
                "months": months,
                "device_count": device_count,
                "discount": discount,
            },
        }

        payment = await self.create_payment_async(payload)
        return payment.id, payment.confirmation.confirmation_url

    # ---------------------------------------------------------
    # Ожидание подтверждения оплаты
    # ---------------------------------------------------------
    async def poll_payment(self, payment_id):
        for i in range(10):
            status, metadata = await asyncio.to_thread(self.check_payment_status, payment_id)

            if status == "succeeded":
                return True, metadata

            await asyncio.sleep(min(10 * (i + 1), 60))

        return False, None

    async def check_payment_loop(
            self,
            payment_id: str,
            user_id: int,
            username: str,
            months: int,
            device_count: int,
            bot,
    ):
        if user_id in self.active_payment_users:
            return

        self.active_payment_users.add(user_id)

        async with AsyncSessionLocal() as session:
            user_crud = UserCrud(session)
            link_service = LinkService(session)

            try:
                ok, metadata = await self.poll_payment(payment_id)
                if not ok:
                    return

                user = await user_crud.get_user(user_id)

                # Создаем пользователя если его нет
                if not user:
                    user = await user_crud.add_user(user_id=user_id, user_name=username)

                # Продлеваем подписку
                await user_crud.update_date(user_id, months)

                # Достаем текущие ключи
                links = await link_service.get_user_links(user_id)

                # Если ключей нет — пробуем выдать заново
                if not links:
                    links = await link_service.assign_links_to_user(user_id, device_count)

                # Если ключи есть, но устройств стало больше — докидываем недостающие
                if links and len(links) < device_count:
                    missing = device_count - len(links)
                    extra_links = await link_service.assign_links_to_user(user_id, missing)
                    if extra_links:
                        links.extend(extra_links)

                # Если после всех попыток ключей все равно нет — ошибка
                if not links:
                    await bot.send_message(
                        user_id,
                        "❌ Недостаточно доступных VPN-серверов. Свяжитесь с поддержкой."
                    )
                    return

                msg = (
                    "🎉 Оплата прошла успешно!\n\n"
                    "Ваши ключи для подключения (нажмите для копирования):\n\n"
                )

                for link in links:
                    msg += f"<code>{link.link_address}</code>\n\n"

                msg += (
                    "📘 Инструкция по установке и подключению:\n"
                    '<a href="https://telegra.ph/Instrukciya-po-podklyucheniyu-07-14">'
                    "Открыть инструкцию</a>"
                )

                await bot.send_message(user_id, msg, parse_mode="HTML")

            except Exception as e:
                print("[PAYMENT LOOP ERROR]:", e)
                try:
                    await bot.send_message(
                        user_id,
                        "❌ Произошла ошибка при обработке вашей оплаты. Свяжитесь с администратором."
                    )
                except:
                    pass
            finally:
                self.active_payment_users.remove(user_id)
