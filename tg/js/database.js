class Database {
    static async getUserData() {
        // В реальном проекте здесь будет запрос к серверу
        // Сейчас используем localStorage для демонстрации

        const tg = window.Telegram.WebApp;
        const userId = tg.initDataUnsafe?.user?.id || 'default';

        const key = `stellar_${userId}`;
        const data = localStorage.getItem(key);

        if (data) {
            return JSON.parse(data);
        }

        // Данные по умолчанию
        return {
            userId,
            stars: 0,
            tapPower: 1,
            maxEnergy: 100,
            passiveIncome: 0,
            totalClicks: 0,
            todayClicks: 0,
            todayStars: 0,
            totalStars: 0,
            lastDailyReward: null,
            achievements: {
                novice: false,
                amateur: false,
                professional: false
            },
            history: []
        };
    }

    static async saveUserData(data) {
        const tg = window.Telegram.WebApp;
        const userId = tg.initDataUnsafe?.user?.id || 'default';
        const key = `stellar_${userId}`;

        localStorage.setItem(key, JSON.stringify(data));

        // Здесь будет отправка на сервер
    }

    static async getTopUsers(limit = 10) {
        // В реальном проекте здесь будет запрос к серверу
        // Для демонстрации возвращаем тестовые данные

        const users = [];
        for (let i = 1; i <= limit; i++) {
            users.push({
                name: `Player ${i}`,
                stars: Math.floor(Math.random() * 1000000)
            });
        }

        return users.sort((a, b) => b.stars - a.stars);
    }
}