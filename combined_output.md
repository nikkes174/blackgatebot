# 🤖 AI Code Bundle

## 📌 Параметры
- **Files:** `[]`
- **Dirs:** `['.']`
- **Extensions:** `['.css', '.html', '.js', '.json', '.py']`

---


# 📂 Директория: `C:\Users\pride\Desktop\python\VPNTgBot`

## 📁 `.`

## 📄 `bot.py`

```python
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

```

## 📄 `config.py`

```python
import os

from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB")

```

## 📄 `get_project.py`

```python

import argparse
import os
from typing import Set, List

# ✅ Расширения файлов
EXTENSIONS: Set[str] = {".py", ".json", ".html", ".css", ".js"}

# ✅ Игнорируемые директории
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    "env",
    "venv",
    "node_modules",
    "site-packages",
    "hooks",
    "logs",
    "refs",
    "pack",
}

DEFAULT_FILES: List[str] = [

]

DEFAULT_DIRS: List[str] = [

    '.'
         ]


EXTENSION_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".json": "json",
    ".html": "html",
    ".css": "css",
}


def read_file_safe(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            return f"[Ошибка чтения (кодировка): {e}]"
    except Exception as e:
        return f"[Ошибка чтения файла: {e}]"


def should_take_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in EXTENSIONS


def get_lang(filename: str) -> str:
    return EXTENSION_TO_LANG.get(os.path.splitext(filename)[1].lower(), "")


def write_one_file_md(path: str, out, base_dir: str  = None):
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        out.write(f"\n> ❌ **Файл не найден:** `{abs_path}`\n\n")
        return

    rel_path = os.path.relpath(abs_path, base_dir) if base_dir else path
    lang = get_lang(path)

    out.write(f"\n## 📄 `{rel_path}`\n\n")
    out.write(f"```{lang}\n")
    out.write(read_file_safe(abs_path))
    out.write("\n```\n")


def collect_directory_md(root_dir: str, out):
    root_dir = os.path.abspath(root_dir)

    if not os.path.exists(root_dir):
        out.write(f"\n> ❌ **Папка не найдена:** `{root_dir}`\n\n")
        return

    out.write(f"\n# 📂 Директория: `{root_dir}`\n")

    for current_root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
        rel_root = os.path.relpath(current_root, root_dir)

        out.write(f"\n## 📁 `{rel_root}`\n")

        for filename in sorted(files):
            if should_take_file(filename):
                full_path = os.path.join(current_root, filename)
                write_one_file_md(full_path, out, root_dir)


def parse_args():
    p = argparse.ArgumentParser(
        description="Собрать файлы и директории в AI-friendly Markdown."
    )

    p.add_argument("--files", "-f", nargs="*", default=DEFAULT_FILES)
    p.add_argument("--dirs", "-d", nargs="*", default=DEFAULT_DIRS)
    p.add_argument("--out", "-o", default="combined_output.md")

    return p.parse_args()


def main():
    args = parse_args()

    with open(args.out, "w", encoding="utf-8") as out:
        out.write("# 🤖 AI Code Bundle\n\n")
        out.write("## 📌 Параметры\n")
        out.write(f"- **Files:** `{args.files}`\n")
        out.write(f"- **Dirs:** `{args.dirs}`\n")
        out.write(f"- **Extensions:** `{sorted(EXTENSIONS)}`\n")

        out.write("\n---\n\n")

        for fpath in args.files:
            write_one_file_md(fpath, out)

        for dpath in args.dirs:
            collect_directory_md(dpath, out)

    print(f"✅ Готово. Markdown файл: {args.out}")


if __name__ == "__main__":
    main()

```

## 📄 `new_payment.py`

```python
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

    def check_payment_status(self, payment_id: str):
        try:
            payment = Payment.find_one(payment_id)
            return payment.status, payment.metadata
        except Exception:
            return None, None

    async def create_payment_async(self, payload: dict):
        return await asyncio.to_thread(Payment.create, payload)

    async def get_discount_by_ref_count(
        self, ref_crud: ReferralCrud, user_id: int
    ) -> int:
        ref_count, _ = await ref_crud.get_user_ref_stats(user_id)

        if ref_count >= 20:
            return 100
        if ref_count >= 10:
            return 25
        if ref_count >= 5:
            return 10
        return 0

    async def create_payment(
        self,
        ref_crud: ReferralCrud,
        user_id: int,
        months: int,
        device_count: int,
    ):
        return_url = "https://t.me/BlackGateGuard_bot"

        if months == 1:

            if device_count == 1:
                base_price = 120
            else:
                base_price = 100 * device_count

        elif months == 6:

            if device_count == 1:
                base_price = 500
            else:
                base_price = 80 * 6 * device_count

        else:
            raise ValueError(f"Неизвестный срок подписки: {months}")

        discount = await self.get_discount_by_ref_count(ref_crud, user_id)

        amount = base_price * (100 - discount) / 100
        if amount <= 0:
            raise RuntimeError(
                "Сумма платежа равна 0 — YooKassa не принимает такие платежи."
            )

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

    async def poll_payment(self, payment_id):
        for i in range(10):
            status, metadata = await asyncio.to_thread(
                self.check_payment_status, payment_id
            )

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

                if not user:
                    user = await user_crud.add_user(
                        user_id=user_id, user_name=username
                    )

                await user_crud.update_date(user_id, months)

                links = await link_service.get_user_links(user_id)

                if not links:
                    links = await link_service.assign_links_to_user(
                        user_id, device_count
                    )

                if links and len(links) < device_count:
                    missing = device_count - len(links)
                    extra_links = await link_service.assign_links_to_user(
                        user_id, missing
                    )
                    if extra_links:
                        links.extend(extra_links)

                if not links:
                    await bot.send_message(
                        user_id,
                        "❌ Недостаточно доступных VPN-серверов. Свяжитесь с поддержкой.",
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
                        "❌ Произошла ошибка при обработке вашей оплаты. Свяжитесь с администратором.",
                    )
                except:
                    pass
            finally:
                self.active_payment_users.remove(user_id)

```

## 📄 `utils.py`

```python
import asyncio
from datetime import datetime, timedelta

import pytz
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.crud_user import UserCrud
from tgbot.keyboards.inline import period_subscriptions

MOSCOW_TZ = pytz.timezone("Europe/Moscow")


import pytz

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
            user_crud = UserCrud(session)
            users = await user_crud.get_all_users()

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
            continue

        except Exception as e:
            print(f"[NOTIFY ERROR] user={user.user_id}: {e}")

    return notified

```

## 📄 `vpn_utils.py`

```python
import os
import json
import uuid
import random
import string
import requests
from dotenv import load_dotenv

load_dotenv()


class X3:
    def __init__(self, host=None, login=None, password=None, base=None):

        self.host = (host or os.getenv("X3_HOST", "http://148.222.186.138:39922")).rstrip("/")
        base_raw = base or os.getenv("X3_BASE", "K1NUNCbkeGEEBOblC2")
        self.base = "/" + base_raw.lstrip("/")

        self.login = login or os.getenv("LOGIN", "")
        self.password = password or os.getenv("PASSWORD", "")

        self.s = requests.Session()
        self.token = None

        self.login_api()

    # ---------------------------------------------------------
    # ЛОГИН — СТАРЫЙ URL, КОТОРЫЙ У ТЕБЯ РЕАЛЬНО РАБОТАЕТ
    # ---------------------------------------------------------
    def login_api(self):
        url = f"{self.host}{self.base}/login"
        r = self.s.post(url, json={"username": self.login, "password": self.password})

        data = r.json()
        if data.get("success"):
            self.token = r.cookies.get("3x-ui")
            return True

        raise RuntimeError("LOGIN FAILED")    # ---------------------------------------------------------
    # ПРАВИЛЬНЫЙ API для inbound'ов — /panel/api/...
    # ---------------------------------------------------------
    def list_inbounds(self):
        url = f"{self.host}{self.base}/panel/api/inbounds/list"
        print("GET INBOUNDS:", url)

        r = self.s.get(url)
        print("LIST STATUS:", r.status_code)
        print("LIST TEXT:", r.text[:200])

        try:
            return r.json()
        except:
            raise RuntimeError("INBOUNDS RESPONSE NOT JSON")

    # ---------------------------------------------------------
    # ДОБАВЛЕНИЕ КЛИЕНТА
    # ---------------------------------------------------------
    def add_client(self, inbound_id: int, user_id: int):
        # Обязательно повторный логин — панель часто дропает сессию
        self.login_api()

        # 1. Получаем inbound'ы
        data = self.list_inbounds()
        if not data.get("success"):
            return None

        inbound = next((i for i in data["obj"] if i["id"] == inbound_id), None)
        if inbound is None:
            return None

        # 2. Разбор settings
        try:
            settings = json.loads(inbound["settings"])
        except:
            return None

        clients = settings.get("clients", [])

        # 3. Создаём нового клиента
        new_uuid = str(uuid.uuid4())
        new_subid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

        new_client = {
            "id": new_uuid,
            "email": f"user_{user_id}",
            "remark": f"user_{user_id}",
            "flow": "",
            "limitIp": 0,
            "totalGB": 0,
            "expiryTime": 0,
            "enable": True,
            "tgId": "",
            "subId": new_subid,
            "comment": "",
            "reset": 0
        }

        clients.append(new_client)
        settings["clients"] = clients

        # 4. Обновлённый inbound payload
        payload = {
            "id": inbound_id,
            "up": inbound["up"],
            "down": inbound["down"],
            "total": inbound["total"],
            "remark": inbound["remark"],
            "enable": inbound["enable"],
            "expiryTime": inbound["expiryTime"],
            "listen": inbound.get("listen", ""),
            "port": inbound["port"],
            "protocol": inbound["protocol"],
            "settings": json.dumps(settings, ensure_ascii=False),
            "streamSettings": inbound["streamSettings"],
            "tag": inbound["tag"]
        }

        # ВАЖНО — правильный URL update
        url = f"{self.host}{self.base}/panel/api/inbounds/update/{inbound_id}"

        # ВАЖНО — передаём cookie токен
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"3x-ui={self.token}"
        }

        r = self.s.post(url, data=payload, headers=headers)

        if '"success":true' in r.text:
            return new_uuid

        return None

    def generate_link(self, client_uuid: str, user_id: int) -> str:
        host = "148.222.186.138"
        port = 443
        pbk = "lfA7_Apsl8-tTxNLS3RfPq2qxrVxfXTLhoLmGd_uKCg"
        sni = "max.ru"
        sid = "b5430da5739bd4df"

        return (
            f"vless://{client_uuid}@{host}:{port}"
            f"?type=tcp"
            f"&encryption=none"
            f"&security=reality"
            f"&pbk={pbk}"
            f"&fp=chrome"
            f"&sni={sni}"
            f"&sid={sid}"
            f"&spx=%2F"
            f"#BlackGate-{user_id}"
        )

```

## 📁 `.ruff_cache`

## 📁 `.ruff_cache\0.12.11`

## 📁 `db`

## 📄 `db\crud_link.py`

```python
from sqlalchemy import func, select
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

```

## 📄 `db\crud_referral.py`

```python
from sqlalchemy import func, select
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
                Referral.referrer_id == referrer_id,
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
            select(func.count(Referral.id)).where(
                Referral.referrer_id == user_id
            )
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

```

## 📄 `db\crud_trial.py`

```python
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import TrialUser


class TrialCrud:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_trial_user(self, user_id: int):
        stmt = select(TrialUser).where(TrialUser.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def add_trial_user(self, user_id: int, username: str):
        trial_user = TrialUser(
            user_id=user_id, user_name=username, last_trial_start=date.today()
        )

        self.session.add(trial_user)
        await self.session.flush()

        return trial_user

```

## 📄 `db\crud_user.py`

```python
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

    async def get_all_users(self):
        result = await self.session.execute(
            select(UserModes)
        )
        return result.scalars().all()
```

## 📄 `db\db.py`

```python
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import DB_URL

engine = create_async_engine(
    DB_URL,
    echo=False,
    poolclass=NullPool,  # Важно!
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

```

## 📄 `db\models.py`

```python
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModes(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, unique=True, nullable=False
    )
    user_name: Mapped[Optional[str]] = mapped_column(String(255))
    end_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    end_trial_period: Mapped[Optional[Date]] = mapped_column(
        Date, nullable=True
    )

    links: Mapped[List[LinkModel]] = relationship(
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
        nullable=True,
    )

    user: Mapped[Optional[UserModes]] = relationship(back_populates="links")


class TrialUser(Base):
    __tablename__ = "trial_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_trial_start: Mapped[Optional[Date]] = mapped_column(Date)


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    referrer_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True
    )

```

## 📁 `Files`

## 📁 `scripts`

## 📁 `scripts\alembic`

## 📁 `scripts\postgres`

## 📁 `tgbot`

## 📄 `tgbot\__init__.py`

```python

```

## 📄 `tgbot\config.py`

```python
from dataclasses import dataclass
from typing import Optional

from environs import Env


@dataclass
class DbConfig:

    host: str
    password: str
    user: str
    database: str
    port: int = 5432

    # For SQLAlchemy
    def construct_sqlalchemy_url(
        self, driver="asyncpg", host=None, port=None
    ) -> str:
        from sqlalchemy.engine.url import URL

        if not host:
            host = self.host
        if not port:
            port = self.port
        uri = URL.create(
            drivername=f"postgresql+{driver}",
            username=self.user,
            password=self.password,
            host=host,
            port=port,
            database=self.database,
        )
        return uri.render_as_string(hide_password=False)

    @staticmethod
    def from_env(env: Env):
        host = env.str("DB_HOST")
        password = env.str("POSTGRES_PASSWORD")
        user = env.str("POSTGRES_USER")
        database = env.str("POSTGRES_DB")
        port = env.int("DB_PORT", 5432)
        return DbConfig(
            host=host,
            password=password,
            user=user,
            database=database,
            port=port,
        )


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool

    @staticmethod
    def from_env(env: Env):
        token = env.str("BOT_TOKEN")

        # ADMINS может отсутствовать → используем default=[]
        admins_raw = env.list("ADMINS", default=[])

        # безопасное преобразование: если ADMINS пуст — admin_ids = []
        admin_ids = [int(x) for x in admins_raw if x]

        use_redis = env.bool("USE_REDIS", default=False)

        return TgBot(token=token, admin_ids=admin_ids, use_redis=use_redis)


@dataclass
class RedisConfig:
    redis_pass: Optional[str]
    redis_port: Optional[int]
    redis_host: Optional[str]

    def dsn(self) -> str:
        if self.redis_pass:
            return f"redis://:{self.redis_pass}@{self.redis_host}:{self.redis_port}/0"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/0"

    @staticmethod
    def from_env(env: Env):
        redis_pass = env.str("REDIS_PASSWORD")
        redis_port = env.int("REDIS_PORT")
        redis_host = env.str("REDIS_HOST")

        return RedisConfig(
            redis_pass=redis_pass, redis_port=redis_port, redis_host=redis_host
        )


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    misc: Miscellaneous
    db: Optional[DbConfig] = None
    redis: Optional[RedisConfig] = None


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot.from_env(env),
        # db=DbConfig.from_env(env),
        # redis=RedisConfig.from_env(env),
        misc=Miscellaneous(),
    )

```

## 📁 `tgbot\filters`

## 📄 `tgbot\filters\__init__.py`

```python

```

## 📄 `tgbot\filters\admin.py`

```python
from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.config import Config


class AdminFilter(BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Message, config: Config) -> bool:
        return (obj.from_user.id in config.tg_bot.admin_ids) == self.is_admin

```

## 📁 `tgbot\handlers`

## 📄 `tgbot\handlers\__init__.py`

```python
"""Import all routers and add them to routers_list."""

from .user import user_router

routers_list = [
    user_router,
]

__all__ = [
    "routers_list",
]

```

## 📄 `tgbot\handlers\admin.py`

```python
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tgbot.keyboards.inline import admin_panel

admin_router = Router()

ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]


@admin_router.message(Command("admin_panel"))
async def open_admin_panel(message: Message):
    user_id = message.from_user.id

    if user_id not in ADMINS:
        await message.answer("⛔️ Нет доступа")
        return

    await message.answer("🛠 Панель администратора", reply_markup=admin_panel())


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

```

## 📄 `tgbot\handlers\echo.py`

```python
from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hcode

echo_router = Router()


@echo_router.message(F.text, StateFilter(None))
async def bot_echo(message: types.Message):
    text = ["Эхо без состояния.", "Сообщения:", message.text]

    await message.answer("\n".join(text))


@echo_router.message(F.text)
async def bot_echo_all(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    text = [
        f"Эхо в состоянии {hcode(state_name)}",
        "Содержание сообщения:",
        hcode(message.text),
    ]
    await message.answer("\n".join(text))

```

## 📄 `tgbot\handlers\user.py`

```python
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

```

## 📁 `tgbot\keyboards`

## 📄 `tgbot\keyboards\__init__.py`

```python

```

## 📄 `tgbot\keyboards\inline.py`

```python
from aiogram.utils.keyboard import InlineKeyboardBuilder


def first_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👁‍‍️ПРОБНЫЙ ПЕРИОД👁‍", callback_data="test_period")
    builder.button(
        text="️‍💳ТАРИФЫ 💳", callback_data="paying_for_subscriptions"
    )
    builder.button(
        text="⚡️Система скидок⚡️",
        url="https://telegra.ph/Sistema-skidok-07-24",
    )
    builder.button(
        text="🔗Реферальная ссылка🔗", callback_data="our_reff_link"
    )
    builder.button(
        text="⁉️ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ⁉️",
        url="https://telegra.ph/Instrukciya-po-podklyucheniyu-07-14",
    )
    builder.button(
        text="⚙️Связь с менеджером⚙️", url="https://t.me/@BlackGateSupp"
    )
    builder.button(
        text="ℹ️Ознакомление с офертойℹ️",
        url="https://telegra.ph/PUBLICHNAYA-OFERTA-09-01-3",
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def period_subscriptions():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥1 МЕСЯЦ🔥", callback_data="one_mouth")
    builder.button(text="️🖤6 МЕСЯЦЕВ🖤", callback_data="six_mouth")
    builder.button(text="Назад 🔙️", callback_data="back_to_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


def to_back_two():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад 🔙️", callback_data="back_to_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


def to_back():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⁉️ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ⁉️",
        url="https://telegra.ph/Instrukciya-po-podklyucheniyu-07-14",
    )
    builder.button(text="Назад 🔙️", callback_data="back_to_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


def trail_button():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="️🚀Активировать пробный период", callback_data="active_test"
    )
    builder.button(
        text="⁉️ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ⁉️",
        url="https://telegra.ph/Instrukciya-po-podklyucheniyu-07-14",
    )
    builder.button(text="Назад 🔙️", callback_data="back_to_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


def admin_panel():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💬Сообщение всем пользователям", callback_data="send_all"
    )
    builder.button(text="❗️Сообщение пользователю", callback_data="send_user")
    builder.button(text="🔍Проверка подписок", callback_data="to_chek")
    builder.button(text="Назад 🔙️", callback_data="back_to_menu")
    builder.adjust(1, 1)
    return builder.as_markup()


def subscription_renewal():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Продлить на 1 МЕСЯЦ/120 руб.🔥",
        callback_data="one_mouth_renewal",
    )
    builder.button(
        text="Продлить ️6 МЕСЯЦЕВ/500 руб.🖤", callback_data="six_mouth_renewal"
    )
    builder.button(text="Назад 🔙️", callback_data="back_to_menu")
    builder.adjust(1, 1)
    return builder.as_markup()

```

## 📁 `tgbot\middlewares`

## 📄 `tgbot\middlewares\__init__.py`

```python

```

## 📄 `tgbot\middlewares\config.py`

```python
from collections.abc import Awaitable
from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config) -> None:
        self.config = config

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        data["config"] = self.config
        return await handler(event, data)

```

## 📄 `tgbot\middlewares\db_session_middleware.py`

```python
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

```

## 📁 `tgbot\misc`

## 📄 `tgbot\misc\__init__.py`

```python

```

## 📄 `tgbot\misc\states.py`

```python
from aiogram.fsm.state import State, StatesGroup


class City(StatesGroup):
    choice = State()


class Toy(StatesGroup):
    choice = State()

```

## 📁 `tgbot\services`

## 📄 `tgbot\services\__init__.py`

```python

```

## 📄 `tgbot\services\broadcaster.py`

```python
import asyncio
import logging
from typing import Union

from aiogram import Bot, exceptions
from aiogram.types import InlineKeyboardMarkup


async def send_message(
    bot: Bot,
    user_id: Union[int, str],
    text: str,
    disable_notification: bool = False,
    reply_markup: InlineKeyboardMarkup = None,
) -> bool:

    try:
        await bot.send_message(
            user_id,
            text,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
        )
    except exceptions.TelegramBadRequest:
        logging.error("Telegram server says - Bad Request: chat not found")
    except exceptions.TelegramForbiddenError:
        logging.error(f"Target [ID:{user_id}]: got TelegramForbiddenError")
    except exceptions.TelegramRetryAfter as e:
        logging.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.retry_after} seconds."
        )
        await asyncio.sleep(e.retry_after)
        return await send_message(
            bot, user_id, text, disable_notification, reply_markup
        )  # Recursive call
    except exceptions.TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcast(
    bot: Bot,
    users: list[Union[str, int]],
    text: str,
    disable_notification: bool = False,
    reply_markup: InlineKeyboardMarkup = None,
) -> int:
    """
    Simple broadcaster.
    :param bot: Bot instance.
    :param users: List of users.
    :param text: Text of the message.
    :param disable_notification: Disable notification or not.
    :param reply_markup: Reply markup.
    :return: Count of messages.
    """
    count = 0
    try:
        for user_id in users:
            if await send_message(
                bot, user_id, text, disable_notification, reply_markup
            ):
                count += 1
            await asyncio.sleep(
                0.05
            )  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logging.info(f"{count} messages successful sent.")

    return count

import asyncio
from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramBadRequest,
)

async def safe_broadcast(
    *,
    bot: Bot,
    users: list,
    text: str,
    delay: float = 0.05,  # 20 msg/sec
) -> dict:
    sent = 0
    blocked = 0
    failed = 0

    for user in users:
        try:
            await bot.send_message(user.user_id, text)
            sent += 1
            await asyncio.sleep(delay)

        except TelegramForbiddenError:
            blocked += 1  # бот заблокирован
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await bot.send_message(user.user_id, text)
            sent += 1
        except TelegramBadRequest:
            failed += 1
        except Exception:
            failed += 1

    return {
        "sent": sent,
        "blocked": blocked,
        "failed": failed,
        "total": len(users),
    }

```
