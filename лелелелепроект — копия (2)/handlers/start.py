from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from keyboards.inline import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start"""
    await message.answer(
        "👋 <b>Привет! Я менеджер подписок.</b>\n\n"
        "Я помогу тебе отслеживать все твои подписки "
        "и вовремя напомню о их окончании.\n\n"
        "🔔 Уведомление придёт за <b>2 дня</b> до окончания подписки.\n\n"
        "Выбери действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu"""
    await message.answer(
        "📱 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "📱 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Помощь"""
    await callback.message.edit_text(
        "ℹ️ <b>Как пользоваться ботом</b>\n\n"
        "1️⃣ Нажми <b>«Добавить подписку»</b>\n"
        "2️⃣ Выбери платформу из списка или введи свою\n"
        "3️⃣ Укажи дату окончания или выбери длительность\n"
        "4️⃣ При желании укажи цену\n"
        "5️⃣ Подтверди добавление\n\n"
        "🔔 Бот пришлёт уведомление за <b>2 дня</b> до окончания.\n\n"
        "📋 В разделе <b>«Мои подписки»</b> можно:\n"
        "• Просмотреть все подписки\n"
        "• Удалить ненужные\n"
        "• Продлить существующие\n\n"
        "<b>Команды:</b>\n"
        "/start — Запуск бота\n"
        "/menu — Главное меню\n"
        "/add — Добавить подписку\n"
        "/list — Мои подписки",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()