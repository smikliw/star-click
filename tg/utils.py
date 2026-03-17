import re
from datetime import datetime


def format_number(num: int) -> str:
    """Форматирование больших чисел"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def escape_markdown(text: str) -> str:
    """Экранирование спецсимволов для Markdown"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))


def get_achievement_emoji(stars: int) -> str:
    """Эмодзи достижения по количеству звезд"""
    if stars >= 1_000_000:
        return "👑 Профессионал"
    elif stars >= 100_000:
        return "⭐ Любитель"
    elif stars >= 1_000:
        return "🌱 Новичок"
    return "🆕 Новичок"


def format_time_ago(timestamp: str) -> str:
    """Форматирование времени (был(а) онлайн)"""
    if not timestamp:
        return "никогда"

    try:
        dt = datetime.fromisoformat(timestamp)
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} ч. назад"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} мин. назад"
        else:
            return "только что"
    except:
        return "неизвестно"