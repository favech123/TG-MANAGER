import asyncio
import logging
from datetime import date

from aiogram import Bot

from config import config
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class NotificationScheduler:
    def __init__(self, bot: Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self._task: asyncio.Task | None = None
    
    def start(self):
        """Запуск планировщика"""
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("🔔 Планировщик уведомлений запущен")
    
    def stop(self):
        """Остановка планировщика"""
        if self._task:
            self._task.cancel()
            logger.info("🔔 Планировщик уведомлений остановлен")
    
    async def _scheduler_loop(self):
        """Основной цикл проверки"""
        while True:
            try:
                await self._check_and_notify()
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
            
            # Ждём указанный интервал
            await asyncio.sleep(config.CHECK_INTERVAL_MINUTES * 60)
    
    async def _check_and_notify(self):
        """Проверка и отправка уведомлений"""
        logger.info("🔍 Проверяю подписки...")
        
        expiring_subs = await self.db.get_expiring_subscriptions(
            config.NOTIFY_DAYS_BEFORE
        )
        
        for sub in expiring_subs:
            try:
                days_left = sub.days_left
                
                if days_left <= 0:
                    text = (
                        f"🔴 <b>Подписка истекла!</b>\n\n"
                        f"📌 {sub.platform}\n"
                        f"📅 Дата окончания: {sub.end_date.strftime('%d.%m.%Y')}\n"
                    )
                elif days_left == 1:
                    text = (
                        f"🟡 <b>Подписка истекает завтра!</b>\n\n"
                        f"📌 {sub.platform}\n"
                        f"📅 Дата окончания: {sub.end_date.strftime('%d.%m.%Y')}\n"
                    )
                else:
                    text = (
                        f"🟡 <b>Подписка скоро истекает!</b>\n\n"
                        f"📌 {sub.platform}\n"
                        f"📅 Дата окончания: {sub.end_date.strftime('%d.%m.%Y')}\n"
                        f"⏳ Осталось: {days_left} дн.\n"
                    )
                
                if sub.is_recurring:
                    text += "\n🔄 Подписка с автопродлением — проверь, нужно ли отменить."
                else:
                    text += "\n💡 Не забудь продлить, если нужно!"
                
                await self.bot.send_message(
                    chat_id=sub.user_id,
                    text=text,
                    parse_mode="HTML",
                )
                
                await self.db.mark_notified(sub.id)
                logger.info(
                    f"✅ Уведомление отправлено: user={sub.user_id}, "
                    f"platform={sub.platform}"
                )
                
            except Exception as e:
                logger.error(
                    f"Ошибка отправки уведомления user={sub.user_id}: {e}"
                )