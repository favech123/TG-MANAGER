from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

from config import config
from database.models import Subscription


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить подписку", 
            callback_data="add_subscription"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Мои подписки", 
            callback_data="my_subscriptions"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Помощь", 
            callback_data="help"
        )
    )
    return builder.as_markup()


def platform_selection_keyboard() -> InlineKeyboardMarkup:
    """Выбор платформы"""
    builder = InlineKeyboardBuilder()
    
    for platform in config.POPULAR_PLATFORMS:
        builder.row(
            InlineKeyboardButton(
                text=platform,
                callback_data=f"platform:{platform}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Ввести своё название",
            callback_data="platform:custom"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def duration_keyboard() -> InlineKeyboardMarkup:
    """Быстрый выбор длительности подписки"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="1 неделя", callback_data="duration:7"),
        InlineKeyboardButton(text="2 недели", callback_data="duration:14"),
    )
    builder.row(
        InlineKeyboardButton(text="1 месяц", callback_data="duration:30"),
        InlineKeyboardButton(text="3 месяца", callback_data="duration:90"),
    )
    builder.row(
        InlineKeyboardButton(text="6 месяцев", callback_data="duration:180"),
        InlineKeyboardButton(text="1 год", callback_data="duration:365"),
    )
    builder.row(
        InlineKeyboardButton(
            text="📅 Ввести дату вручную",
            callback_data="duration:custom"
        )
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    
    return builder.as_markup()


def recurring_keyboard() -> InlineKeyboardMarkup:
    """Автопродление?"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Да", callback_data="recurring:yes"),
        InlineKeyboardButton(text="🔚 Нет", callback_data="recurring:no"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def price_keyboard() -> InlineKeyboardMarkup:
    """Хочет ли указать цену"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="price:skip")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def currency_keyboard() -> InlineKeyboardMarkup:
    """Выбор валюты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="₽ RUB", callback_data="currency:₽"),
        InlineKeyboardButton(text="$ USD", callback_data="currency:$"),
        InlineKeyboardButton(text="€ EUR", callback_data="currency:€"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение добавления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no"),
    )
    return builder.as_markup()


def subscription_detail_keyboard(sub_id: int) -> InlineKeyboardMarkup:
    """Действия с конкретной подпиской"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"delete:{sub_id}"
        ),
        InlineKeyboardButton(
            text="📅 Продлить",
            callback_data=f"extend:{sub_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к списку",
            callback_data="my_subscriptions"
        )
    )
    return builder.as_markup()


def subscriptions_list_keyboard(
    subscriptions: List[Subscription],
) -> InlineKeyboardMarkup:
    """Список подписок (кнопки)"""
    builder = InlineKeyboardBuilder()
    
    for sub in subscriptions:
        builder.row(
            InlineKeyboardButton(
                text=f"{sub.status_emoji} {sub.platform} — {sub.days_left} дн.",
                callback_data=f"sub_detail:{sub.id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить подписку",
            callback_data="add_subscription"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def delete_confirm_keyboard(sub_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"delete_confirm:{sub_id}"
        ),
        InlineKeyboardButton(
            text="❌ Нет",
            callback_data=f"sub_detail:{sub_id}"
        ),
    )
    return builder.as_markup()


def extend_keyboard(sub_id: int) -> InlineKeyboardMarkup:
    """Продление подписки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="1 месяц", callback_data=f"extend_do:{sub_id}:30"
        ),
        InlineKeyboardButton(
            text="3 месяца", callback_data=f"extend_do:{sub_id}:90"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="6 месяцев", callback_data=f"extend_do:{sub_id}:180"
        ),
        InlineKeyboardButton(
            text="1 год", callback_data=f"extend_do:{sub_id}:365"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=f"sub_detail:{sub_id}"
        )
    )
    return builder.as_markup()