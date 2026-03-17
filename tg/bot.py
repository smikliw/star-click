import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.markdown import hbold, hlink
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import Config
from keyboards import get_main_keyboard, get_admin_keyboard, get_back_keyboard
from database import db
from utils import format_number, get_achievement_emoji, format_time_ago

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота с новым синтаксисом Aiogram 3.x
bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# ============== КОМАНДЫ ==============

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user

    # Добавляем пользователя в БД
    is_new = await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Приветственное сообщение
    welcome_text = (
        f"🌟 <b>Добро пожаловать в Stellar Clicke, {user.first_name}!</b>\n\n"
        f"Это кликер с Telegram Mini App. Нажимай на звезду, "
        f"зарабатывай очки и прокачивай свой кликер!\n\n"
        f"🎮 <b>Что можно делать:</b>\n"
        f"• Нажимать на звезду и получать очки\n"
        f"• Улучшать силу тапа, энергию и пассивный доход\n"
        f"• Соревноваться с другими игроками\n"
        f"• Получать достижения\n\n"
        f"👇 <b>Нажми кнопку ниже, чтобы начать игру!</b>"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

    # Если пользователь пришел по реферальной ссылке
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user.id:
            await handle_referral(user.id, referrer_id)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "❓ <b>Помощь по Stellar Clicke</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Эта справка\n"
        "/stats - Моя статистика\n"
        "/top - Топ игроков\n"
        "/referral - Реферальная программа\n\n"
        "<b>Как играть:</b>\n"
        "1️⃣ Нажми '🌟 Играть в Stellar Clicke'\n"
        "2️⃣ Кликай по звезде в центре\n"
        "3️⃣ Улучшай характеристики\n"
        "4️⃣ Соревнуйся в топе\n\n"
        "Удачи! 🚀"
    )

    await message.answer(
        help_text,
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Личная статистика пользователя"""
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)

    if not user_data:
        await message.answer("Сначала начни игру через /start")
        return

    stats_text = (
        f"📊 <b>Статистика {message.from_user.first_name}</b>\n\n"
        f"⭐ Звезд: <b>{format_number(user_data.get('stars', 0))}</b>\n"
        f"👆 Кликов: <b>{format_number(user_data.get('clicks', 0))}</b>\n"
        f"⚡ Сила тапа: <b>{user_data.get('tap_power', 1)}</b>\n"
        f"🔋 Энергия: <b>{user_data.get('energy', 100)}</b>\n"
        f"💫 Пассивный доход: <b>{user_data.get('passive_income', 0)}/сек</b>\n"
        f"🏆 Достижение: <b>{get_achievement_emoji(user_data.get('stars', 0))}</b>\n"
        f"📅 В игре с: <b>{user_data.get('joined_date', 'неизвестно')[:10]}</b>\n"
        f"🕐 Последний раз: <b>{format_time_ago(user_data.get('last_activity', ''))}</b>"
    )

    # Создаем клавиатуру с Web App кнопкой
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔄 Обновить из игры",
                    web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}?user_id={user_id}")
                )
            ],
            [
                KeyboardButton(text="🔙 Назад")
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        stats_text,
        reply_markup=keyboard
    )


@dp.message(Command("top"))
async def cmd_top(message: Message):
    """Топ 10 игроков"""
    top_users = await db.get_top_users(10)

    if not top_users:
        await message.answer("Пока нет игроков в топе")
        return

    text = "🏆 <b>Топ 10 игроков</b>\n\n"

    for i, user in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
        name = user.get('name', 'Unknown')
        stars = format_number(user.get('stars', 0))
        text += f"{medal} {i}. {name} — <b>{stars}</b> ⭐\n"

    await message.answer(text)


@dp.message(Command("referral"))
async def cmd_referral(message: Message):
    """Реферальная программа"""
    user_id = message.from_user.id

    ref_link = f"https://t.me/{Config.BOT_USERNAME}?start={user_id}"

    text = (
        "🤝 <b>Реферальная программа</b>\n\n"
        "Приглашай друзей и получай бонусы!\n"
        "• За каждого друга +100 ⭐\n"
        "• Когда друг наберет 1000 ⭐, ты получишь еще +500 ⭐\n\n"
        f"Твоя ссылка:\n<code>{ref_link}</code>\n\n"
        "Просто отправь её друзьям!"
    )

    await message.answer(
        text,
        reply_markup=get_main_keyboard()
    )


# ============== ОБРАБОТЧИКИ СООБЩЕНИЙ ==============

@dp.message(F.text == "📊 Моя статистика")
async def handle_stats_button(message: Message):
    await cmd_stats(message)


@dp.message(F.text == "🏆 Топ игроков")
async def handle_top_button(message: Message):
    await cmd_top(message)


@dp.message(F.text == "❓ Помощь")
async def handle_help_button(message: Message):
    await cmd_help(message)


@dp.message(F.text == "🔙 Назад")
async def handle_back_button(message: Message):
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )


@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """Обработка данных из Web App"""
    data = message.web_app_data.data

    try:
        game_data = json.loads(data)

        user_id = message.from_user.id

        # Обновляем статистику пользователя
        await db.update_user_stats(user_id, {
            'stars': game_data.get('stars', 0),
            'clicks': game_data.get('clicks', 0),
            'tap_power': game_data.get('tap_power', 1),
            'energy': game_data.get('energy', 100),
            'passive_income': game_data.get('passive_income', 0)
        })

        # Отправляем подтверждение
        stars = game_data.get('stars', 0)
        await message.answer(
            f"✅ Данные сохранены!\n"
            f"Текущий баланс: {format_number(stars)} ⭐"
        )

    except Exception as e:
        logging.error(f"Error processing web app data: {e}")
        await message.answer("❌ Ошибка при сохранении данных")


# ============== АДМИН ПАНЕЛЬ ==============

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ панель"""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("⛔ Доступ запрещен")
        return

    stats = await db.get_total_stats()

    text = (
        "👑 <b>Админ панель</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"📊 Активных сегодня: <b>{stats['active_today']}</b>\n"
        f"⭐ Всего звезд: <b>{format_number(stats['total_stars'])}</b>\n"
        f"👆 Всего кликов: <b>{format_number(stats['total_clicks'])}</b>\n\n"
        "Выберите действие:"
    )

    await message.answer(
        text,
        reply_markup=get_admin_keyboard()
    )


@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    await callback.answer()

    if callback.from_user.id not in Config.ADMIN_IDS:
        await callback.message.answer("⛔ Доступ запрещен")
        return

    stats = await db.get_total_stats()

    text = (
        "📊 <b>Детальная статистика</b>\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"📊 Активных сегодня: {stats['active_today']}\n"
        f"⭐ Всего звезд: {format_number(stats['total_stars'])}\n"
        f"👆 Всего кликов: {format_number(stats['total_clicks'])}\n"
        f"📈 Среднее звезд: {format_number(stats['total_stars'] / max(stats['total_users'], 1))}"
    )

    await callback.message.answer(text)


@dp.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    await callback.answer()

    if callback.from_user.id not in Config.ADMIN_IDS:
        return

    await callback.message.answer("👥 Функция в разработке")


# ============== ОБРАБОТЧИК РЕФЕРАЛОВ ==============

async def handle_referral(new_user_id: int, referrer_id: int):
    """Обработка рефералов"""
    # Начисляем бонус пригласившему
    referrer_data = await db.get_user(referrer_id)
    if referrer_data:
        current_stars = referrer_data.get('stars', 0)
        await db.update_user_stats(referrer_id, {
            'stars': current_stars + 100
        })

        # Добавляем в список рефералов
        referrals = referrer_data.get('referrals', [])
        referrals.append(new_user_id)
        await db.update_user_stats(referrer_id, {'referrals': referrals})

    # Уведомляем пригласившего
    try:
        await bot.send_message(
            referrer_id,
            f"🎉 По вашему приглашению присоединился новый игрок!\n"
            f"Вы получили +100 ⭐"
        )
    except:
        pass


# ============== ЗАПУСК БОТА ==============

async def set_commands():
    """Установка команд бота"""
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Помощь"),
        types.BotCommand(command="stats", description="Моя статистика"),
        types.BotCommand(command="top", description="Топ игроков"),
        types.BotCommand(command="referral", description="Реферальная программа"),
        types.BotCommand(command="admin", description="Админ панель")
    ]
    await bot.set_my_commands(commands)


async def main():
    """Главная функция запуска"""
    await set_commands()
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())