from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from config import Config


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура с Web App кнопкой"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🌟 Играть в Stellar Clicke",
                    web_app=WebAppInfo(url=Config.WEBAPP_URL)
                )
            ],
            [
                KeyboardButton(text="📊 Моя статистика"),
                KeyboardButton(text="🏆 Топ игроков")
            ],
            [
                KeyboardButton(text="❓ Помощь")
            ]
        ],
        resize_keyboard=True
    )

    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для админов"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
                InlineKeyboardButton(text="🔧 Настройки", callback_data="admin_settings")
            ]
        ]
    )

    return keyboard


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Кнопка назад"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard