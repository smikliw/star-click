import sqlite3
import json
from datetime import datetime, timedelta
import hashlib
import hmac
import os


class Database:
    def __init__(self, db_name="startap.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Инициализация таблиц базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 1000,
                max_energy INTEGER DEFAULT 1000,
                tap_power INTEGER DEFAULT 1,
                passive_level INTEGER DEFAULT 0,
                total_clicks INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                last_energy_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_bonus_date DATE,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users(telegram_id)
            )
        ''')

        # Таблица улучшений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                cost INTEGER,
                effect_type TEXT,
                effect_value INTEGER,
                max_level INTEGER DEFAULT 10
            )
        ''')

        # Таблица купленных улучшений пользователями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_upgrades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                upgrade_id INTEGER,
                level INTEGER DEFAULT 1,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (upgrade_id) REFERENCES upgrades(id),
                UNIQUE(user_id, upgrade_id)
            )
        ''')

        # Таблица ежедневных бонусов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_number INTEGER,
                claimed BOOLEAN DEFAULT 0,
                claimed_date DATE,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, day_number)
            )
        ''')

        # Таблица заданий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                reward INTEGER,
                quest_type TEXT,
                target_value INTEGER DEFAULT 1
            )
        ''')

        # Таблица выполненных заданий (исправлено: добавлено EXISTS)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quest_id INTEGER,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            )
        ''')

        conn.commit()

        # Добавляем базовые улучшения, если их нет
        self.init_upgrades()
        # Добавляем базовые задания
        self.init_quests()

        conn.close()

    def init_upgrades(self):
        """Добавление базовых улучшений"""
        conn = self.get_connection()
        cursor = conn.cursor()

        upgrades = [
            ("Сила тапа", "Увеличивает количество звезд за клик", 100, "tap_power", 1, 100),
            ("Энергия", "Увеличивает максимальный запас энергии", 200, "max_energy", 500, 50),
            ("Пассивный доход", "Автоматический заработок звезд", 500, "passive_income", 1, 100)
        ]

        for upgrade in upgrades:
            cursor.execute('''
                INSERT OR IGNORE INTO upgrades (name, description, cost, effect_type, effect_value, max_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', upgrade)

        conn.commit()
        conn.close()

    def init_quests(self):
        """Добавление базовых заданий"""
        conn = self.get_connection()
        cursor = conn.cursor()

        quests = [
            ("Новичок", "Сделай 100 кликов", 500, "clicks", 100),
            ("Энергичный", "Накопи 1000 энергии", 300, "energy", 1000),
            ("Богач", "Заработай 1000 звезд", 1000, "balance", 1000)
        ]

        for quest in quests:
            cursor.execute('''
                INSERT OR IGNORE INTO quests (name, description, reward, quest_type, target_value)
                VALUES (?, ?, ?, ?, ?)
            ''', quest)

        conn.commit()
        conn.close()

    def create_user(self, telegram_id, username=None, first_name=None, last_name=None, referred_by=None):
        """Создание нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Генерируем реферальный код
        referral_code = hashlib.md5(f"{telegram_id}{datetime.now()}".encode()).hexdigest()[:8]

        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name, referral_code, referred_by))

            conn.commit()

            # Создаем записи для ежедневных бонусов
            for day in range(1, 8):
                cursor.execute('''
                    INSERT INTO daily_bonuses (user_id, day_number)
                    VALUES (?, ?)
                ''', (telegram_id, day))

            # Создаем записи для заданий
            cursor.execute("SELECT id FROM quests")
            quests = cursor.fetchall()
            for quest in quests:
                cursor.execute('''
                    INSERT INTO user_quests (user_id, quest_id)
                    VALUES (?, ?)
                ''', (telegram_id, quest[0]))

            conn.commit()

            # Если пользователь пришел по рефералке, начисляем бонус
            if referred_by:
                self.add_referral_bonus(telegram_id, referred_by)

            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user(self, telegram_id):
        """Получение данных пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users WHERE telegram_id = ?
        ''', (telegram_id,))

        user = cursor.fetchone()
        if user:
            columns = [description[0] for description in cursor.description]
            user_dict = dict(zip(columns, user))
            conn.close()
            return user_dict
        conn.close()
        return None

    def update_energy(self, telegram_id):
        """Обновление энергии на основе времени"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT energy, max_energy, last_energy_update FROM users WHERE telegram_id = ?
        ''', (telegram_id,))

        result = cursor.fetchone()
        if result:
            energy, max_energy, last_update = result
            last_update = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
            seconds_passed = (datetime.now() - last_update).seconds

            # Восстанавливаем 5 энергии в секунду
            energy_to_add = seconds_passed * 5
            new_energy = min(energy + energy_to_add, max_energy)

            cursor.execute('''
                UPDATE users 
                SET energy = ?, last_energy_update = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (new_energy, telegram_id))

            conn.commit()

        conn.close()

    def add_click(self, telegram_id):
        """Обработка клика"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Сначала обновляем энергию
        self.update_energy(telegram_id)

        cursor.execute('''
            SELECT balance, energy, tap_power FROM users WHERE telegram_id = ?
        ''', (telegram_id,))

        user = cursor.fetchone()
        if user and user[1] >= 1:  # Проверяем энергию
            new_energy = user[1] - 1
            new_balance = user[0] + user[2]

            cursor.execute('''
                UPDATE users 
                SET balance = ?, energy = ?, total_clicks = total_clicks + 1, total_earned = total_earned + ?
                WHERE telegram_id = ?
            ''', (new_balance, new_energy, user[2], telegram_id))

            conn.commit()
            conn.close()

            # Обновляем прогресс заданий
            self.update_quest_progress(telegram_id, "clicks", 1)
            self.update_quest_progress(telegram_id, "balance", new_balance)

            return True

        conn.close()
        return False

    def buy_upgrade(self, telegram_id, upgrade_id):
        """Покупка улучшения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем информацию об улучшении
        cursor.execute('SELECT * FROM upgrades WHERE id = ?', (upgrade_id,))
        upgrade = cursor.fetchone()

        if not upgrade:
            conn.close()
            return False

        # Получаем текущий уровень улучшения у пользователя
        cursor.execute('''
            SELECT level FROM user_upgrades 
            WHERE user_id = ? AND upgrade_id = ?
        ''', (telegram_id, upgrade_id))

        user_upgrade = cursor.fetchone()
        current_level = user_upgrade[0] if user_upgrade else 0

        if current_level >= upgrade[6]:  # Проверка max_level
            conn.close()
            return False

        # Проверяем баланс
        cursor.execute('SELECT balance FROM users WHERE telegram_id = ?', (telegram_id,))
        balance = cursor.fetchone()[0]

        cost = upgrade[3] * (current_level + 1)  # Стоимость растет с уровнем

        if balance < cost:
            conn.close()
            return False

        # Списываем средства
        cursor.execute('UPDATE users SET balance = balance - ? WHERE telegram_id = ?', (cost, telegram_id))

        # Обновляем или создаем запись об улучшении
        if user_upgrade:
            cursor.execute('''
                UPDATE user_upgrades SET level = level + 1, purchased_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND upgrade_id = ?
            ''', (telegram_id, upgrade_id))
        else:
            cursor.execute('''
                INSERT INTO user_upgrades (user_id, upgrade_id, level)
                VALUES (?, ?, 1)
            ''', (telegram_id, upgrade_id))

        # Применяем эффект улучшения
        effect_type = upgrade[4]
        effect_value = upgrade[5]

        if effect_type == "tap_power":
            cursor.execute('UPDATE users SET tap_power = tap_power + ? WHERE telegram_id = ?',
                           (effect_value, telegram_id))
        elif effect_type == "max_energy":
            cursor.execute('UPDATE users SET max_energy = max_energy + ?, energy = energy + ? WHERE telegram_id = ?',
                           (effect_value, effect_value, telegram_id))
        elif effect_type == "passive_income":
            cursor.execute('UPDATE users SET passive_level = passive_level + ? WHERE telegram_id = ?',
                           (effect_value, telegram_id))

        conn.commit()
        conn.close()
        return True

    def get_leaderboard(self, limit=10):
        """Получение таблицы лидеров"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT username, first_name, balance FROM users 
            ORDER BY balance DESC LIMIT ?
        ''', (limit,))

        leaderboard = cursor.fetchall()
        conn.close()

        return [{"name": row[1] or row[0] or "Аноним", "balance": row[2]} for row in leaderboard]

    def claim_daily_bonus(self, telegram_id):
        """Получение ежедневного бонуса"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем, получал ли сегодня бонус
        cursor.execute('''
            SELECT last_bonus_date FROM users WHERE telegram_id = ?
        ''', (telegram_id,))

        last_bonus_row = cursor.fetchone()
        last_bonus = last_bonus_row[0] if last_bonus_row else None
        today = datetime.now().date()

        if last_bonus:
            try:
                last_bonus_date = datetime.strptime(last_bonus, '%Y-%m-%d').date()
                if last_bonus_date == today:
                    conn.close()
                    return False
            except:
                pass

        # Получаем текущий день бонуса
        cursor.execute('''
            SELECT day_number FROM daily_bonuses 
            WHERE user_id = ? AND claimed = 0 
            ORDER BY day_number LIMIT 1
        ''', (telegram_id,))

        result = cursor.fetchone()
        if result:
            day = result[0]
            bonus_amount = day * 100

            # Начисляем бонус
            cursor.execute('UPDATE users SET balance = balance + ?, last_bonus_date = ? WHERE telegram_id = ?',
                           (bonus_amount, today, telegram_id))

            # Отмечаем день как полученный
            cursor.execute('''
                UPDATE daily_bonuses SET claimed = 1, claimed_date = ?
                WHERE user_id = ? AND day_number = ?
            ''', (today, telegram_id, day))

            conn.commit()
            conn.close()
            return True

        # Если все дни получены, сбрасываем
        cursor.execute('DELETE FROM daily_bonuses WHERE user_id = ?', (telegram_id,))
        for day in range(1, 8):
            cursor.execute('''
                INSERT INTO daily_bonuses (user_id, day_number)
                VALUES (?, ?)
            ''', (telegram_id, day))

        conn.commit()
        conn.close()
        return self.claim_daily_bonus(telegram_id)

    def update_quest_progress(self, telegram_id, quest_type, progress_amount):
        """Обновление прогресса заданий"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT uq.id, uq.progress, q.target_value, q.reward 
            FROM user_quests uq
            JOIN quests q ON uq.quest_id = q.id
            WHERE uq.user_id = ? AND q.quest_type = ? AND uq.completed = 0
        ''', (telegram_id, quest_type))

        quests = cursor.fetchall()

        for quest in quests:
            quest_id, progress, target, reward = quest
            new_progress = min(progress + progress_amount, target)

            cursor.execute('''
                UPDATE user_quests SET progress = ? WHERE id = ?
            ''', (new_progress, quest_id))

            if new_progress >= target:
                # Задание выполнено
                cursor.execute('''
                    UPDATE user_quests SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?
                ''', (quest_id,))

                # Начисляем награду
                cursor.execute('UPDATE users SET balance = balance + ? WHERE telegram_id = ?', (reward, telegram_id))

        conn.commit()
        conn.close()

    def add_referral_bonus(self, new_user_id, referrer_id):
        """Начисление бонуса за реферала"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Начисляем бонус пригласившему
        cursor.execute('UPDATE users SET balance = balance + 1000 WHERE telegram_id = ?', (referrer_id,))

        # Начисляем бонус новому пользователю
        cursor.execute('UPDATE users SET balance = balance + 500 WHERE telegram_id = ?', (new_user_id,))

        conn.commit()
        conn.close()

    def get_user_upgrades(self, telegram_id):
        """Получение всех улучшений пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT u.name, u.description, u.cost, u.effect_type, u.effect_value, u.max_level, 
                   COALESCE(uu.level, 0) as level
            FROM upgrades u
            LEFT JOIN user_upgrades uu ON u.id = uu.upgrade_id AND uu.user_id = ?
        ''', (telegram_id,))

        upgrades = cursor.fetchall()
        conn.close()

        return [
            {
                "name": row[0],
                "description": row[1],
                "base_cost": row[2],
                "effect_type": row[3],
                "effect_value": row[4],
                "max_level": row[5],
                "level": row[6]
            }
            for row in upgrades
        ]

    def apply_passive_income(self):
        """Применение пассивного дохода для всех пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT telegram_id, passive_level FROM users WHERE passive_level > 0')
        users = cursor.fetchall()

        for user in users:
            telegram_id, passive_level = user
            cursor.execute('UPDATE users SET balance = balance + ? WHERE telegram_id = ?', (passive_level, telegram_id))

        conn.commit()
        conn.close()

    def get_referral_count(self, telegram_id):
        """Получение количества приглашенных друзей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (telegram_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count