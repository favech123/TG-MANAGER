import aiosqlite
from datetime import date, datetime
from typing import List, Optional

from database.models import Subscription


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def init_db(self):
        """Создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    description TEXT,
                    price REAL,
                    currency TEXT DEFAULT '₽',
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    is_recurring INTEGER DEFAULT 0,
                    notified INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON subscriptions(user_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_end_date 
                ON subscriptions(end_date)
            """)
            
            await db.commit()
    
    def _row_to_subscription(self, row) -> Subscription:
        """Конвертация строки БД в объект Subscription"""
        return Subscription(
            id=row[0],
            user_id=row[1],
            platform=row[2],
            description=row[3],
            price=row[4],
            currency=row[5],
            start_date=date.fromisoformat(row[6]),
            end_date=date.fromisoformat(row[7]),
            is_recurring=bool(row[8]),
            notified=bool(row[9]),
            created_at=datetime.fromisoformat(row[10]),
        )
    
    async def add_subscription(self, sub: Subscription) -> int:
        """Добавить подписку, возвращает ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO subscriptions 
                (user_id, platform, description, price, currency, 
                 start_date, end_date, is_recurring, notified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sub.user_id,
                    sub.platform,
                    sub.description,
                    sub.price,
                    sub.currency,
                    sub.start_date.isoformat(),
                    sub.end_date.isoformat(),
                    int(sub.is_recurring),
                    int(sub.notified),
                    sub.created_at.isoformat(),
                ),
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """Все подписки пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY end_date ASC",
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_subscription(row) for row in rows]
    
    async def get_subscription_by_id(self, sub_id: int) -> Optional[Subscription]:
        """Получить подписку по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM subscriptions WHERE id = ?",
                (sub_id,),
            )
            row = await cursor.fetchone()
            return self._row_to_subscription(row) if row else None
    
    async def delete_subscription(self, sub_id: int) -> bool:
        """Удалить подписку"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM subscriptions WHERE id = ?",
                (sub_id,),
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_expiring_subscriptions(self, days: int) -> List[Subscription]:
        """
        Подписки, которые истекают через `days` дней 
        и по которым ещё не отправлено уведомление
        """
        target_date = date.today()
        from datetime import timedelta
        target_end = target_date + timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT * FROM subscriptions 
                WHERE end_date <= ? 
                  AND end_date >= ?
                  AND notified = 0
                ORDER BY end_date ASC
                """,
                (target_end.isoformat(), target_date.isoformat()),
            )
            rows = await cursor.fetchall()
            return [self._row_to_subscription(row) for row in rows]
    
    async def mark_notified(self, sub_id: int):
        """Пометить подписку как уведомлённую"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE subscriptions SET notified = 1 WHERE id = ?",
                (sub_id,),
            )
            await db.commit()
    
    async def reset_notification(self, sub_id: int):
        """Сбросить флаг уведомления"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE subscriptions SET notified = 0 WHERE id = ?",
                (sub_id,),
            )
            await db.commit()
    
    async def update_end_date(self, sub_id: int, new_end_date: date):
        """Обновить дату окончания (продление)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE subscriptions SET end_date = ?, notified = 0 WHERE id = ?",
                (new_end_date.isoformat(), sub_id),
            )
            await db.commit()
    
    async def get_all_user_ids(self) -> List[int]:
        """Получить всех уникальных пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT user_id FROM subscriptions"
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]