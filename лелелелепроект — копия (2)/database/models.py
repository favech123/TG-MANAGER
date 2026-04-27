from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Subscription:
    id: Optional[int]
    user_id: int
    platform: str
    description: Optional[str]
    price: Optional[float]
    currency: str
    start_date: date
    end_date: date
    is_recurring: bool
    notified: bool
    created_at: datetime

    @property
    def days_left(self) -> int:
        """Сколько дней осталось до окончания"""
        delta = self.end_date - date.today()
        return delta.days

    @property
    def total_days(self) -> int:
        """Общая длительность подписки"""
        delta = self.end_date - self.start_date
        return max(delta.days, 1)  # минимум 1 чтобы не делить на 0

    @property
    def percent_left(self) -> float:
        """Процент оставшегося времени (0.0 - 1.0)"""
        if self.total_days == 0:
            return 0.0
        return max(self.days_left / self.total_days, 0.0)

    @property
    def is_expired(self) -> bool:
        return self.end_date < date.today()

    @property
    def status_emoji(self) -> str:
        days = self.days_left
        percent = self.percent_left

        # Истекла
        if days < 0:
            return "🔴"

        # Критично: осталось 2 дня или меньше (всегда красный)
        if days <= 2:
            return "🔴"

        # Дальше смотрим по проценту оставшегося времени
        if percent <= 0.15:
            return "🟠"    # Осталось ≤15% — оранжевый
        elif percent <= 0.30:
            return "🟡"    # Осталось ≤30% — жёлтый
        else:
            return "🟢"    # Осталось >30% — зелёный

    def format_info(self) -> str:
        """Форматированная информация о подписке"""
        status = self.status_emoji
        days = self.days_left
        percent = self.percent_left

        if days < 0:
            days_text = f"Истекла {abs(days)} дн. назад"
        elif days == 0:
            days_text = "Истекает сегодня!"
        elif days == 1:
            days_text = "Истекает завтра!"
        else:
            days_text = f"Осталось {days} дн. ({percent:.0%})"

        price_text = ""
        if self.price:
            price_text = f"\n💰 Цена: {self.price} {self.currency}"

        desc_text = ""
        if self.description:
            desc_text = f"\n📝 {self.description}"

        recurring_text = "🔄 Автопродление" if self.is_recurring else "🔚 Разовая"

        return (
            f"{status} <b>{self.platform}</b>\n"
            f"📅 {self.start_date.strftime('%d.%m.%Y')} → {self.end_date.strftime('%d.%m.%Y')}\n"
            f"⏳ {days_text}"
            f"{price_text}"
            f"{desc_text}\n"
            f"{recurring_text}"
        )