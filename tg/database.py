import json
import aiofiles
import os
from datetime import datetime
from typing import Optional, Dict, List, Any


class Database:
    def __init__(self):
        self.data_file = "users_data.json"
        self.users: Dict[str, Dict] = {}
        self.load_data()

    def load_data(self):
        """Загрузка данных из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            self.users = {}

    async def save_data(self):
        """Сохранение данных в файл"""
        async with aiofiles.open(self.data_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.users, ensure_ascii=False, indent=2))

    async def add_user(self, user_id: int, username: str, first_name: str, last_name: Optional[str] = None) -> bool:
        """Добавление нового пользователя"""
        user_id = str(user_id)

        if user_id not in self.users:
            self.users[user_id] = {
                'id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'joined_date': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'stars': 0,
                'clicks': 0,
                'tap_power': 1,
                'energy': 100,
                'passive_income': 0,
                'achievements': [],
                'referrals': []
            }
            await self.save_data()
            return True
        else:
            # Обновляем последнюю активность
            self.users[user_id]['last_activity'] = datetime.now().isoformat()
            await self.save_data()
            return False

    async def update_user_stats(self, user_id: int, stats: Dict[str, Any]):
        """Обновление статистики пользователя"""
        user_id = str(user_id)
        if user_id in self.users:
            self.users[user_id].update(stats)
            self.users[user_id]['last_activity'] = datetime.now().isoformat()
            await self.save_data()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение данных пользователя"""
        return self.users.get(str(user_id))

    async def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Топ пользователей по звездам"""
        users_list = []
        for uid, data in self.users.items():
            users_list.append({
                'name': data.get('first_name', 'Unknown'),
                'username': data.get('username', ''),
                'stars': data.get('stars', 0)
            })

        # Сортируем по звездам
        users_list.sort(key=lambda x: x['stars'], reverse=True)
        return users_list[:limit]

    async def get_total_stats(self) -> Dict[str, Any]:
        """Общая статистика бота"""
        total_users = len(self.users)
        total_stars = sum(user.get('stars', 0) for user in self.users.values())
        total_clicks = sum(user.get('clicks', 0) for user in self.users.values())

        return {
            'total_users': total_users,
            'total_stars': total_stars,
            'total_clicks': total_clicks,
            'active_today': self.get_active_today()
        }

    def get_active_today(self) -> int:
        """Пользователи активные сегодня"""
        today = datetime.now().date()
        count = 0

        for user in self.users.values():
            last = user.get('last_activity', '')
            if last:
                try:
                    last_date = datetime.fromisoformat(last).date()
                    if last_date == today:
                        count += 1
                except:
                    pass

        return count


# Создаем глобальный экземпляр БД
db = Database()