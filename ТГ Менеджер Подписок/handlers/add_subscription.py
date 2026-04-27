from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import date, timedelta, datetime

from keyboards.inline import (
    platform_selection_keyboard,
    duration_keyboard,
    recurring_keyboard,
    price_keyboard,
    currency_keyboard,
    confirm_keyboard,
    main_menu_keyboard,
)
from database.models import Subscription
from database.db_manager import DatabaseManager
from utils.date_parser import parse_date, validate_end_date

router = Router()


class AddSubscriptionStates(StatesGroup):
    choosing_platform = State()
    entering_custom_platform = State()
    choosing_duration = State()
    entering_custom_date = State()
    choosing_recurring = State()
    entering_price = State()
    choosing_currency = State()
    confirming = State()


# ---------- Начало добавления ----------

@router.callback_query(F.data == "add_subscription")
async def start_add_subscription(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления"""
    await state.clear()
    await state.set_state(AddSubscriptionStates.choosing_platform)
    
    await callback.message.edit_text(
        "➕ <b>Добавление подписки</b>\n\n"
        "Выбери платформу из списка или введи своё название:",
        reply_markup=platform_selection_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("add"))
async def cmd_add_subscription(message: Message, state: FSMContext):
    """Команда /add"""
    await state.clear()
    await state.set_state(AddSubscriptionStates.choosing_platform)
    
    await message.answer(
        "➕ <b>Добавление подписки</b>\n\n"
        "Выбери платформу из списка или введи своё название:",
        reply_markup=platform_selection_keyboard(),
        parse_mode="HTML",
    )


# ---------- Выбор платформы ----------

@router.callback_query(
    AddSubscriptionStates.choosing_platform,
    F.data.startswith("platform:"),
)
async def platform_selected(callback: CallbackQuery, state: FSMContext):
    """Платформа выбрана из списка"""
    platform = callback.data.split(":", 1)[1]
    
    if platform == "custom":
        await state.set_state(AddSubscriptionStates.entering_custom_platform)
        await callback.message.edit_text(
            "✏️ <b>Введи название платформы:</b>",
            parse_mode="HTML",
        )
    else:
        await state.update_data(platform=platform)
        await state.set_state(AddSubscriptionStates.choosing_duration)
        await callback.message.edit_text(
            f"✅ Платформа: <b>{platform}</b>\n\n"
            f"⏰ Выбери длительность подписки или введи дату окончания:",
            reply_markup=duration_keyboard(),
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.message(AddSubscriptionStates.entering_custom_platform)
async def custom_platform_entered(message: Message, state: FSMContext):
    """Ввод своего названия платформы"""
    platform = message.text.strip()
    
    if len(platform) > 100:
        await message.answer("❌ Название слишком длинное (макс. 100 символов). Попробуй ещё:")
        return
    
    if len(platform) < 1:
        await message.answer("❌ Название не может быть пустым. Попробуй ещё:")
        return
    
    await state.update_data(platform=platform)
    await state.set_state(AddSubscriptionStates.choosing_duration)
    
    await message.answer(
        f"✅ Платформа: <b>{platform}</b>\n\n"
        f"⏰ Выбери длительность подписки или введи дату окончания:",
        reply_markup=duration_keyboard(),
        parse_mode="HTML",
    )


# ---------- Выбор даты ----------

@router.callback_query(
    AddSubscriptionStates.choosing_duration,
    F.data.startswith("duration:"),
)
async def duration_selected(callback: CallbackQuery, state: FSMContext):
    """Длительность выбрана"""
    value = callback.data.split(":", 1)[1]
    
    if value == "custom":
        await state.set_state(AddSubscriptionStates.entering_custom_date)
        await callback.message.edit_text(
            "📅 <b>Введи дату окончания подписки</b>\n\n"
            "Формат: <code>ДД.ММ.ГГГГ</code>\n"
            "Пример: <code>25.12.2025</code>",
            parse_mode="HTML",
        )
    else:
        days = int(value)
        today = date.today()
        end_date = today + timedelta(days=days)
        
        await state.update_data(
            start_date=today.isoformat(),
            end_date=end_date.isoformat(),
        )
        await state.set_state(AddSubscriptionStates.choosing_recurring)
        
        data = await state.get_data()
        await callback.message.edit_text(
            f"✅ Платформа: <b>{data['platform']}</b>\n"
            f"📅 Окончание: <b>{end_date.strftime('%d.%m.%Y')}</b>\n\n"
            f"🔄 Подписка с автопродлением?",
            reply_markup=recurring_keyboard(),
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.message(AddSubscriptionStates.entering_custom_date)
async def custom_date_entered(message: Message, state: FSMContext):
    """Ввод даты вручную"""
    parsed = parse_date(message.text)
    
    if parsed is None:
        await message.answer(
            "❌ Не могу распознать дату.\n\n"
            "Используй формат: <code>ДД.ММ.ГГГГ</code>\n"
            "Пример: <code>25.12.2025</code>",
            parse_mode="HTML",
        )
        return
    
    is_valid, error_msg = validate_end_date(parsed)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    today = date.today()
    await state.update_data(
        start_date=today.isoformat(),
        end_date=parsed.isoformat(),
    )
    await state.set_state(AddSubscriptionStates.choosing_recurring)
    
    data = await state.get_data()
    await message.answer(
        f"✅ Платформа: <b>{data['platform']}</b>\n"
        f"📅 Окончание: <b>{parsed.strftime('%d.%m.%Y')}</b>\n\n"
        f"🔄 Подписка с автопродлением?",
        reply_markup=recurring_keyboard(),
        parse_mode="HTML",
    )


# ---------- Автопродление ----------

@router.callback_query(
    AddSubscriptionStates.choosing_recurring,
    F.data.startswith("recurring:"),
)
async def recurring_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор автопродления"""
    value = callback.data.split(":", 1)[1]
    is_recurring = value == "yes"
    
    await state.update_data(is_recurring=is_recurring)
    await state.set_state(AddSubscriptionStates.entering_price)
    
    data = await state.get_data()
    recurring_text = "🔄 Автопродление" if is_recurring else "🔚 Разовая"
    
    await callback.message.edit_text(
        f"✅ Платформа: <b>{data['platform']}</b>\n"
        f"📅 Окончание: <b>{date.fromisoformat(data['end_date']).strftime('%d.%m.%Y')}</b>\n"
        f"{recurring_text}\n\n"
        f"💰 Введи стоимость подписки (число) или пропусти:",
        reply_markup=price_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- Цена ----------

@router.callback_query(
    AddSubscriptionStates.entering_price,
    F.data == "price:skip",
)
async def price_skipped(callback: CallbackQuery, state: FSMContext):
    """Цена пропущена"""
    await state.update_data(price=None, currency="₽")
    await _show_confirmation(callback.message, state, edit=True)
    await callback.answer()


@router.message(AddSubscriptionStates.entering_price)
async def price_entered(message: Message, state: FSMContext):
    """Ввод цены"""
    text = message.text.strip().replace(",", ".")
    
    try:
        price = float(text)
        if price <= 0:
            raise ValueError
        if price > 1_000_000:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введи корректную цену (положительное число).\n"
            "Пример: <code>299</code> или <code>9.99</code>",
            reply_markup=price_keyboard(),
            parse_mode="HTML",
        )
        return
    
    await state.update_data(price=price)
    await state.set_state(AddSubscriptionStates.choosing_currency)
    
    await message.answer(
        f"💰 Цена: <b>{price}</b>\n\n"
        f"Выбери валюту:",
        reply_markup=currency_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(
    AddSubscriptionStates.choosing_currency,
    F.data.startswith("currency:"),
)
async def currency_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор валюты"""
    currency = callback.data.split(":", 1)[1]
    await state.update_data(currency=currency)
    await _show_confirmation(callback.message, state, edit=True)
    await callback.answer()


# ---------- Подтверждение ----------

async def _show_confirmation(message, state: FSMContext, edit: bool = False):
    """Показать данные для подтверждения"""
    data = await state.get_data()
    await state.set_state(AddSubscriptionStates.confirming)
    
    end_date = date.fromisoformat(data["end_date"])
    start_date = date.fromisoformat(data["start_date"])
    recurring_text = "🔄 Автопродление" if data.get("is_recurring") else "🔚 Разовая"
    
    price_text = ""
    if data.get("price"):
        price_text = f"\n💰 Цена: {data['price']} {data.get('currency', '₽')}"
    
    text = (
        "📋 <b>Проверь данные подписки:</b>\n\n"
        f"📌 Платформа: <b>{data['platform']}</b>\n"
        f"📅 Начало: <b>{start_date.strftime('%d.%m.%Y')}</b>\n"
        f"📅 Окончание: <b>{end_date.strftime('%d.%m.%Y')}</b>\n"
        f"⏳ Осталось: <b>{(end_date - date.today()).days} дн.</b>"
        f"{price_text}\n"
        f"{recurring_text}\n\n"
        f"Всё верно?"
    )
    
    if edit:
        await message.edit_text(
            text, reply_markup=confirm_keyboard(), parse_mode="HTML"
        )
    else:
        await message.answer(
            text, reply_markup=confirm_keyboard(), parse_mode="HTML"
        )


@router.callback_query(
    AddSubscriptionStates.confirming,
    F.data.startswith("confirm:"),
)
async def confirm_subscription(
    callback: CallbackQuery, state: FSMContext, db: DatabaseManager
):
    """Подтверждение или отмена"""
    value = callback.data.split(":", 1)[1]
    
    if value == "no":
        await state.clear()
        await callback.message.edit_text(
            "❌ Добавление отменено.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return
    
    # Сохранение в БД
    data = await state.get_data()
    
    subscription = Subscription(
        id=None,
        user_id=callback.from_user.id,
        platform=data["platform"],
        description=None,
        price=data.get("price"),
        currency=data.get("currency", "₽"),
        start_date=date.fromisoformat(data["start_date"]),
        end_date=date.fromisoformat(data["end_date"]),
        is_recurring=data.get("is_recurring", False),
        notified=False,
        created_at=datetime.now(),
    )
    
    sub_id = await db.add_subscription(subscription)
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Подписка добавлена!</b>\n\n"
        f"📌 {data['platform']}\n"
        f"📅 До {date.fromisoformat(data['end_date']).strftime('%d.%m.%Y')}\n\n"
        f"🔔 Я напомню тебе за 2 дня до окончания.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("✅ Подписка сохранена!")


# ---------- Отмена ----------

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена любого действия"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()