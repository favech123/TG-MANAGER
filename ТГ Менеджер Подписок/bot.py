import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import config
from database.db_manager import DatabaseManager
from services.scheduler import NotificationScheduler
from handlers import start, add_subscription, my_subscriptions

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    # Инициализация бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Инициализация БД
    db = DatabaseManager(config.DATABASE_PATH)
    await db.init_db()
    
    # Диспетчер
    dp = Dispatcher()
    
    # Middleware для инъекции db во все хендлеры
    @dp.update.outer_middleware()
    async def db_middleware(handler, event, data):
        data["db"] = db
        return await handler(event, data)
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(add_subscription.router)
    dp.include_router(my_subscriptions.router)
    
    # Планировщик уведомлений
    scheduler = NotificationScheduler(bot, db)
    
    # Startup/shutdown
    async def on_startup():
        logger.info("🚀 Бот запущен!")
        scheduler.start()
    
    async def on_shutdown():
        logger.info("🛑 Бот остановлен")
        scheduler.stop()
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())