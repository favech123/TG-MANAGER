from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from datetime import date, timedelta

from keyboards.inline import (
    subscriptions_list_keyboard,
    subscription_detail_keyboard,
    delete_confirm_keyboard,
    extend_keyboard,
    main_menu_keyboard,
)
from database.db_manager import DatabaseManager

router = Router()


@router.callback_query(F.data == "my_subscriptions")
async def show_subscriptions(callback: CallbackQuery, db: DatabaseManager):
    """Показать список подписок"""
    subs = await db.get_user_subscriptions(callback.from_user.id)
    
    if not subs:
        await callback.message.edit_text(
            "📋 <b>У тебя пока нет подписок.</b>\n\n"
            "Нажми <b>«Добавить подписку»</b>, чтобы начать.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return
    
    # Статистика
    active = [s for s in subs if not s.is_expired]
    expired = [s for s in subs if s.is_expired]
    total_monthly = sum(
        (s.price or 0) for s in active
    )
    
    text = (
        f"📋 <b>Твои подписки</b> ({len(active)} активных"
        f"{f', {len(expired)} истекших' if expired else ''})\n\n"
    )
    
    if total_monthly > 0:
        text += f"💰 Общая стоимость: ~{total_monthly:.0f}\n\n"
    
    text += "Нажми на подписку для подробностей:"
    
    await callback.message.edit_text(
        text,
        reply_markup=subscriptions_list_keyboard(subs),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("list"))
async def cmd_list_subscriptions(message: Message, db: DatabaseManager):
    """Команда /list"""
    subs = await db.get_user_subscriptions(message.from_user.id)
    
    if not subs:
        await message.answer(
            "📋 <b>У тебя пока нет подписок.</b>\n\n"
            "Нажми <b>«Добавить подписку»</b>, чтобы начать.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        return
    
    await message.answer(
        f"📋 <b>Твои подписки</b> ({len(subs)} шт.)\n\n"
        "Нажми на подписку для подробностей:",
        reply_markup=subscriptions_list_keyboard(subs),
        parse_mode="HTML",
    )


# ---------- Детали подписки ----------

@router.callback_query(F.data.startswith("sub_detail:"))
async def show_subscription_detail(callback: CallbackQuery, db: DatabaseManager):
    """Детали конкретной подписки"""
    sub_id = int(callback.data.split(":")[1])
    sub = await db.get_subscription_by_id(sub_id)
    
    if not sub:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    if sub.user_id != callback.from_user.id:
        await callback.answer("❌ Это не твоя подписка", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📌 <b>Подписка #{sub.id}</b>\n\n{sub.format_info()}",
        reply_markup=subscription_detail_keyboard(sub.id),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- Удаление ----------

@router.callback_query(F.data.startswith("delete:"))
async def delete_subscription_prompt(callback: CallbackQuery, db: DatabaseManager):
    """Запрос подтверждения удаления"""
    sub_id = int(callback.data.split(":")[1])
    sub = await db.get_subscription_by_id(sub_id)
    
    if not sub or sub.user_id != callback.from_user.id:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"🗑 <b>Удалить подписку?</b>\n\n"
        f"📌 {sub.platform}\n"
        f"📅 До {sub.end_date.strftime('%d.%m.%Y')}\n\n"
        f"Это действие нельзя отменить.",
        reply_markup=delete_confirm_keyboard(sub.id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_confirm:"))
async def delete_subscription_confirmed(
    callback: CallbackQuery, db: DatabaseManager
):
    """Подтверждённое удаление"""
    sub_id = int(callback.data.split(":")[1])
    sub = await db.get_subscription_by_id(sub_id)
    
    if not sub or sub.user_id != callback.from_user.id:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    await db.delete_subscription(sub_id)
    
    await callback.message.edit_text(
        f"✅ Подписка <b>{sub.platform}</b> удалена.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("✅ Удалено!")


# ---------- Продление ----------

@router.callback_query(F.data.startswith("extend:"))
async def extend_subscription_prompt(callback: CallbackQuery, db: DatabaseManager):
    """Выбор срока продления"""
    sub_id = int(callback.data.split(":")[1])
    sub = await db.get_subscription_by_id(sub_id)
    
    if not sub or sub.user_id != callback.from_user.id:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📅 <b>Продление подписки</b>\n\n"
        f"📌 {sub.platform}\n"
        f"📅 Текущая дата окончания: {sub.end_date.strftime('%d.%m.%Y')}\n\n"
        f"На сколько продлить?",
        reply_markup=extend_keyboard(sub.id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("extend_do:"))
async def extend_subscription_do(callback: CallbackQuery, db: DatabaseManager):
    """Выполнение продления"""
    parts = callback.data.split(":")
    sub_id = int(parts[1])
    days = int(parts[2])
    
    sub = await db.get_subscription_by_id(sub_id)
    
    if not sub or sub.user_id != callback.from_user.id:
        await callback.answer("❌ Подписка не найдена", show_alert=True)
        return
    
    # Продлеваем от текущей даты окончания или от сегодня (если истекла)
    base_date = max(sub.end_date, date.today())
    new_end_date = base_date + timedelta(days=days)
    
    await db.update_end_date(sub_id, new_end_date)
    
    await callback.message.edit_text(
        f"✅ <b>Подписка продлена!</b>\n\n"
        f"📌 {sub.platform}\n"
        f"📅 Новая дата окончания: <b>{new_end_date.strftime('%d.%m.%Y')}</b>",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("✅ Продлено!")