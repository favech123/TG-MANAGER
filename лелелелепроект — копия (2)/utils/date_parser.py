from datetime import date, datetime
from typing import Optional


def parse_date(text: str) -> Optional[date]:
    """
    Парсит дату из текста.
    Поддерживаемые форматы:
    - DD.MM.YYYY
    - DD/MM/YYYY
    - DD-MM-YYYY
    - YYYY-MM-DD
    """
    formats = [
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%y",
        "%d/%m/%y",
    ]
    
    text = text.strip()
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt).date()
            return parsed
        except ValueError:
            continue
    
    return None


def validate_end_date(end_date: date) -> tuple[bool, str]:
    """Проверяет, что дата окончания в будущем"""
    today = date.today()
    
    if end_date < today:
        return False, "❌ Дата окончания не может быть в прошлом!"
    
    if end_date == today:
        return False, "❌ Дата окончания не может быть сегодня!"
    
    return True, ""