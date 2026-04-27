import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Явно указываем путь к .env относительно этого файла
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Загружаем .env
loaded = load_dotenv(ENV_PATH)
print(f"📁 Ищу .env по пути: {ENV_PATH}")
print(f"📁 Файл .env существует: {ENV_PATH.exists()}")
print(f"📁 Загружен: {loaded}")
print(f"📁 BOT_TOKEN: {os.getenv('BOT_TOKEN', 'НЕ НАЙДЕН')[:20]}...")


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_PATH: str = "subscriptions.db"
    NOTIFY_DAYS_BEFORE: int = 2
    CHECK_INTERVAL_MINUTES: int = 60

    POPULAR_PLATFORMS: List[str] = field(default_factory=lambda: [
        "Netflix",
        "Spotify",
        "YouTube Premium",
        "Apple Music",
        "Яндекс Плюс",
        "VK Музыка",
        "Adobe Creative Cloud",
        "Microsoft 365",
        "ChatGPT Plus",
        "Telegram Premium",
        "iCloud+",
        "Google One",
        "Amazon Prime",
        "Disney+",
        "HBO Max",
    ])

    def __post_init__(self):
        if not self.BOT_TOKEN:
            raise ValueError(
                f"❌ BOT_TOKEN не найден!\n"
                f"Проверь файл: {ENV_PATH}\n"
                f"Файл существует: {ENV_PATH.exists()}\n\n"
                f"Содержимое .env должно быть:\n"
                f"BOT_TOKEN=твой_токен_от_BotFather"
            )


config = Config()