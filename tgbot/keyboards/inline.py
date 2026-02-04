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
