from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import Database
import hmac
import hashlib
import json
from datetime import datetime
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

app = Flask(__name__, static_folder='templates')
CORS(app)  # Разрешаем кросс-доменные запросы

# Инициализация базы данных
db = Database()

# Токен вашего Telegram бота (теперь из переменной окружения)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8501275776:AAGr1b_4z6IikTZzU6KBSLipYKPHSnHAzzM')

def verify_telegram_data(init_data):
    """Проверка подписи данных от Telegram"""
    if not BOT_TOKEN:
        # Если токен не задан, пропускаем проверку (для разработки)
        return True
    try:
        # Парсим данные
        data = {}
        for item in init_data.split('&'):
            key, value = item.split('=')
            data[key] = value

        # Проверяем hash
        hash_check = data.pop('hash', '')

        # Сортируем и формируем строку для проверки
        sorted_data = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))

        # Создаем secret key
        secret = hashlib.sha256(BOT_TOKEN.encode()).digest()

        # Вычисляем HMAC
        computed_hash = hmac.new(secret, sorted_data.encode(), hashlib.sha256).hexdigest()

        return computed_hash == hash_check
    except Exception as e:
        print(f"Verification error: {e}")
        return False


@app.route('/')
def serve_frontend():
    """Отдача фронтенда"""
    return send_from_directory('templates', 'index.html')


@app.route('/api/init', methods=['POST'])
def init_user():
    """Инициализация пользователя"""
    data = request.json
    init_data = data.get('initData', '')

    # Проверяем подпись (опционально)
    if not verify_telegram_data(init_data):
        return jsonify({"error": "Invalid data"}), 403

    # Получаем данные пользователя
    # В реальности нужно парсить initData, но для простоты используем переданные поля
    telegram_id = data.get('telegram_id')
    if not telegram_id:
        return jsonify({"error": "Missing telegram_id"}), 400

    username = data.get('username', '')
    first_name = data.get('first_name', 'Игрок')
    referred_by = data.get('referral')  # Параметр из start-ссылки

    # Проверяем, существует ли пользователь
    user = db.get_user(telegram_id)

    if not user:
        # Создаем нового пользователя
        db.create_user(telegram_id, username, first_name, None, referred_by)
        user = db.get_user(telegram_id)

    # Обновляем энергию
    db.update_energy(telegram_id)

    # Получаем обновленные данные
    user = db.get_user(telegram_id)
    upgrades = db.get_user_upgrades(telegram_id)

    # Получаем количество рефералов
    referral_count = db.get_referral_count(telegram_id)

    return jsonify({
        "success": True,
        "user": user,
        "upgrades": upgrades,
        "referralCount": referral_count
    })


@app.route('/api/click', methods=['POST'])
def process_click():
    """Обработка клика"""
    data = request.json
    telegram_id = data.get('telegram_id')

    result = db.add_click(telegram_id)

    if result:
        user = db.get_user(telegram_id)
        return jsonify({
            "success": True,
            "balance": user['balance'],
            "energy": user['energy']
        })
    else:
        return jsonify({
            "success": False,
            "error": "Not enough energy"
        }), 400


@app.route('/api/buy_upgrade', methods=['POST'])
def buy_upgrade():
    """Покупка улучшения"""
    data = request.json
    telegram_id = data.get('telegram_id')
    upgrade_id = data.get('upgrade_id')

    result = db.buy_upgrade(telegram_id, upgrade_id)

    if result:
        user = db.get_user(telegram_id)
        upgrades = db.get_user_upgrades(telegram_id)
        return jsonify({
            "success": True,
            "user": user,
            "upgrades": upgrades
        })
    else:
        return jsonify({
            "success": False,
            "error": "Cannot buy upgrade"
        }), 400


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Получение таблицы лидеров"""
    limit = request.args.get('limit', 10, type=int)
    leaderboard = db.get_leaderboard(limit)

    return jsonify({
        "success": True,
        "leaderboard": leaderboard
    })


@app.route('/api/claim_bonus', methods=['POST'])
def claim_bonus():
    """Получение ежедневного бонуса"""
    data = request.json
    telegram_id = data.get('telegram_id')

    result = db.claim_daily_bonus(telegram_id)

    if result:
        user = db.get_user(telegram_id)
        return jsonify({
            "success": True,
            "balance": user['balance']
        })
    else:
        return jsonify({
            "success": False,
            "error": "Bonus already claimed today"
        }), 400


@app.route('/api/user_data', methods=['POST'])
def get_user_data():
    """Получение актуальных данных пользователя"""
    data = request.json
    telegram_id = data.get('telegram_id')

    db.update_energy(telegram_id)
    user = db.get_user(telegram_id)
    upgrades = db.get_user_upgrades(telegram_id)
    referral_count = db.get_referral_count(telegram_id)

    return jsonify({
        "success": True,
        "user": user,
        "upgrades": upgrades,
        "referralCount": referral_count
    })


def passive_income_job():
    """Фоновый процесс для пассивного дохода"""
    while True:
        time.sleep(60)  # Раз в минуту
        db.apply_passive_income()


# Запускаем фоновый процесс
threading.Thread(target=passive_income_job, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
