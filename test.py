import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "7985681666:AAEnw1uIHhKQLA3paqKdYFPxV7QWzsJJ_Lk"

USER_IDS = [


    5650089980,
    7282208453

]

MESSAGE_TEXT = (
    "Здравствуйте, во время выполнения оплаты у нас были тестовые работы. Ваша ссылка на подключение заблокирована.Выполните оплату по новой."
)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    for user_id in USER_IDS:
        try:
            await bot.send_message(user_id, MESSAGE_TEXT)
            print(f"✅ Отправлено: {user_id}")
        except Exception as e:
            print(f"❌ Ошибка {user_id}: {e}")

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
