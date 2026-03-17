class StellarClicker {
    constructor() {
        this.userData = null;
        this.currentPage = 'main';
        this.energy = 100;
        this.maxEnergy = 100;
        this.stars = 0;
        this.tapPower = 1;
        this.passiveIncome = 0;
        this.totalClicks = 0;
        todayClicks: 0,
        todayStars: 0,
        totalStars: 0,
        x2Multiplier = 1;
        x2EndTime = null;
        clickerLevel = 0; // 0 - star, 1 - planet, 2 - system, 3 - universe
        clickerImages = [
            'images/clicker/star.png',
            'images/clicker/planet.png',
            'images/clicker/system.png',
            'images/clicker/universe.png'
        ];

        this.init();
    }

    async init() {
        await this.loadUserData();
        this.setupEventListeners();
        this.startPassiveIncome();
        this.startEnergyRegeneration();
        this.checkX2Bonus();
        this.loadPage('main');
    }

    async loadUserData() {
        // Загрузка данных из базы
        this.userData = await Database.getUserData();
        this.stars = this.userData.stars || 0;
        this.tapPower = this.userData.tapPower || 1;
        this.maxEnergy = this.userData.maxEnergy || 100;
        this.energy = this.maxEnergy;
        this.passiveIncome = this.userData.passiveIncome || 0;
        this.totalClicks = this.userData.totalClicks || 0;
        todayClicks: this.userData.todayClicks || 0,
        todayStars: this.userData.todayStars || 0,
        totalStars: this.userData.totalStars || 0,
        this.updateUI();
    }

    setupEventListeners() {
        // Навигация
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = e.target.dataset.page;
                this.switchPage(page);
            });
        });
    }

    switchPage(page) {
        this.currentPage = page;
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });
        this.loadPage(page);
    }

    loadPage(pageName) {
        fetch(`pages/${pageName}.html`)
            .then(response => response.text())
            .then(html => {
                document.getElementById('content').innerHTML = html;
                this.initPage(pageName);
            })
            .catch(error => {
                console.error('Error loading page:', error);
            });
    }

    initPage(pageName) {
        switch(pageName) {
            case 'main':
                this.initMainPage();
                break;
            case 'upgrades':
                this.initUpgradesPage();
                break;
            case 'rating':
                this.initRatingPage();
                break;
            case 'bonuses':
                this.initBonusesPage();
                break;
            case 'profile':
                this.initProfilePage();
                break;
        }
    }

    initMainPage() {
        const clickerImg = document.querySelector('.clicker-image');
        const starsCounter = document.querySelector('.stars-counter');
        const energyFill = document.querySelector('.energy-fill');
        const energyText = document.querySelector('.energy-text');
        const tapPowerSpan = document.querySelector('.tap-power');
        const passiveIncomeSpan = document.querySelector('.passive-income');

        // Установка изображения кликера
        clickerImg.src = this.clickerImages[this.clickerLevel];

        // Обновление счетчиков
        this.updateMainUI();

        // Обработчик клика по звезде
        clickerImg.addEventListener('click', (e) => {
            this.handleClick(e);
        });
    }

    handleClick(event) {
        if (this.energy <= 0) {
            this.showNotification('❌ Энергия закончилась! Подождите восстановления');
            return;
        }

        // Анимация
        const clicker = event.target;
        clicker.classList.add('animate');
        setTimeout(() => clicker.classList.remove('animate'), 300);

        // Появление звездочек
        this.createStarParticles(event.clientX, event.clientY);

        // Расчет награды
        let reward = this.tapPower * this.x2Multiplier;

        // Обновление статистики
        this.stars += reward;
        this.energy -= 2;
        this.totalClicks++;
        todayClicks++;
        todayStars += reward;
        totalStars += reward;

        // Проверка на изменение кликера
        this.checkClickerEvolution();

        // Проверка достижений
        this.checkAchievements();

        // Обновление UI
        this.updateMainUI();

        // Сохранение в БД
        this.saveUserData();
    }

    createStarParticles(x, y) {
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.className = 'star-particle';
            particle.textContent = '⭐';
            particle.style.left = (x - 10) + 'px';
            particle.style.top = (y - 10) + 'px';
            particle.style.transform = `rotate(${Math.random() * 360}deg)`;
            document.body.appendChild(particle);

            setTimeout(() => particle.remove(), 1000);
        }
    }

    checkClickerEvolution() {
        if (totalStars >= 1000000 && this.clickerLevel < 3) {
            this.clickerLevel = 3;
            document.querySelector('.clicker-image').src = this.clickerImages[3];
        } else if (totalStars >= 100000 && this.clickerLevel < 2) {
            this.clickerLevel = 2;
            document.querySelector('.clicker-image').src = this.clickerImages[2];
        } else if (totalStars >= 10000 && this.clickerLevel < 1) {
            this.clickerLevel = 1;
            document.querySelector('.clicker-image').src = this.clickerImages[1];
        }
    }

    checkAchievements() {
        if (totalStars >= 1000 && !this.userData.achievements.novice) {
            this.unlockAchievement('novice', 'Новичок');
        }
        if (totalStars >= 100000 && !this.userData.achievements.amateur) {
            this.unlockAchievement('amateur', 'Любитель');
        }
        if (totalStars >= 1000000 && !this.userData.achievements.professional) {
            this.unlockAchievement('professional', 'Профессионал');
        }
    }

    unlockAchievement(id, name) {
        this.userData.achievements[id] = true;
        this.addToHistory(`🏆 Получено достижение: ${name}`);
        this.showNotification(`🎉 Новое достижение: ${name}`);
    }

    updateMainUI() {
        const starsCounter = document.querySelector('.stars-counter');
        const energyFill = document.querySelector('.energy-fill');
        const energyText = document.querySelector('.energy-text');
        const tapPowerSpan = document.querySelector('.tap-power');
        const passiveIncomeSpan = document.querySelector('.passive-income');
        const x2Timer = document.querySelector('.x2-timer');

        if (starsCounter) starsCounter.textContent = this.formatNumber(this.stars);
        if (energyFill) {
            const percent = (this.energy / this.maxEnergy) * 100;
            energyFill.style.width = percent + '%';
        }
        if (energyText) energyText.textContent = `${Math.floor(this.energy)}/${this.maxEnergy}`;
        if (tapPowerSpan) tapPowerSpan.textContent = this.tapPower;
        if (passiveIncomeSpan) passiveIncomeSpan.textContent = this.passiveIncome;

        // Обновление таймера x2
        if (x2Timer && this.x2EndTime) {
            const timeLeft = Math.max(0, Math.floor((this.x2EndTime - Date.now()) / 1000));
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            x2Timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    initUpgradesPage() {
        const balanceSpan = document.querySelector('.balance-amount');
        balanceSpan.textContent = this.formatNumber(this.stars);

        // Кнопки улучшений
        document.querySelectorAll('.upgrade-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.buyUpgrade(type);
            });
        });
    }

    buyUpgrade(type) {
        let price = this.getUpgradePrice(type);
        let currentLevel = this.getUpgradeLevel(type);

        if (this.stars < price) {
            this.showNotification('❌ Недостаточно звезд!');
            return;
        }

        this.stars -= price;

        switch(type) {
            case 'tap':
                this.tapPower++;
                this.addToHistory(`⚡ Улучшена сила тапа до ${this.tapPower}`);
                break;
            case 'energy':
                this.maxEnergy += 10;
                this.energy += 10;
                this.addToHistory(`🔋 Улучшена энергия до ${this.maxEnergy}`);
                break;
            case 'passive':
                this.passiveIncome++;
                this.addToHistory(`💫 Улучшен пассивный доход до ${this.passiveIncome}/сек`);
                break;
        }

        this.updateUpgradesUI();
        this.saveUserData();
    }

    getUpgradePrice(type) {
        const level = this.getUpgradeLevel(type);
        const basePrice = type === 'tap' ? 100 : type === 'energy' ? 200 : 500;
        const multiplier = Math.floor(level / 5) + 1;
        return basePrice * multiplier;
    }

    getUpgradeLevel(type) {
        switch(type) {
            case 'tap': return this.tapPower;
            case 'energy': return Math.floor((this.maxEnergy - 100) / 10) + 1;
            case 'passive': return this.passiveIncome;
        }
    }

    initRatingPage() {
        this.loadRating();
    }

    async loadRating() {
        const ratingList = document.querySelector('.rating-list');
        const users = await Database.getTopUsers(10);

        users.forEach((user, index) => {
            const item = document.createElement('div');
            item.className = 'rating-item';
            item.innerHTML = `
                <div class="rating-name">
                    <span class="rating-position">${index + 1}</span>
                    <span>${user.name}</span>
                </div>
                <span class="rating-stars">${this.formatNumber(user.stars)} ⭐</span>
            `;
            ratingList.appendChild(item);
        });
    }

    initBonusesPage() {
        this.updateDailyReward();
        this.loadMissions();
    }

    updateDailyReward() {
        const today = new Date().getDay() || 7;
        const days = document.querySelectorAll('.reward-day');

        days.forEach((day, index) => {
            if (index + 1 === today) {
                day.classList.add('active');
                day.addEventListener('click', () => this.claimDailyReward());
            }
        });
    }

    claimDailyReward() {
        const day = new Date().getDay() || 7;
        const reward = day * 100;

        if (this.userData.lastDailyReward === this.getTodayDate()) {
            this.showNotification('❌ Награда уже получена сегодня!');
            return;
        }

        this.stars += reward;
        this.userData.lastDailyReward = this.getTodayDate();
        this.addToHistory(`🎁 Получена ежедневная награда: ${reward} ⭐`);
        this.showNotification(`✅ Получено ${reward} звезд!`);
        this.saveUserData();
    }

    loadMissions() {
        const missions = [
            { id: 1, name: 'Накликать 1000 звезд', target: 1000, reward: 500 },
            { id: 2, name: 'Улучшить силу тапа до 5', target: 5, reward: 300 },
            { id: 3, name: 'Накопить 5000 энергии', target: 5000, reward: 1000 }
        ];

        const missionsList = document.querySelector('.missions-list');
        missions.forEach(mission => {
            const item = document.createElement('div');
            item.className = 'mission-item';
            item.innerHTML = `
                <span>${mission.name}</span>
                <span class="mission-reward">+${mission.reward} ⭐</span>
            `;
            missionsList.appendChild(item);
        });
    }

    initProfilePage() {
        // Загрузка данных пользователя Telegram
        const tg = window.Telegram.WebApp;
        const user = tg.initDataUnsafe?.user;

        if (user) {
            document.querySelector('.profile-avatar').src = user.photo_url || 'default-avatar.png';
            document.querySelector('.profile-name').textContent = `${user.first_name} ${user.last_name || ''}`;
        }

        // Достижения
        this.loadAchievements();

        // Статистика
        document.querySelector('.total-clicks').textContent = this.formatNumber(this.totalClicks);
        document.querySelector('.today-clicks').textContent = this.formatNumber(todayClicks);
        document.querySelector('.total-stars').textContent = this.formatNumber(totalStars);
        document.querySelector('.today-stars').textContent = this.formatNumber(todayStars);

        // История
        this.loadHistory();
    }

    loadAchievements() {
        const achievements = {
            novice: { name: 'Новичок', stars: 1000 },
            amateur: { name: 'Любитель', stars: 100000 },
            professional: { name: 'Профессионал', stars: 1000000 }
        };

        Object.keys(achievements).forEach(key => {
            const element = document.querySelector(`.achievement-${key}`);
            const img = element.querySelector('.achievement-image');
            const isUnlocked = totalStars >= achievements[key].stars;

            if (isUnlocked) {
                img.src = `images/achievements/${key}.png`;
                element.classList.remove('achievement-locked');
            } else {
                img.src = 'images/achievements/lock.png';
                element.classList.add('achievement-locked');
            }
        });
    }

    addToHistory(text) {
        const historyList = document.querySelector('.history-list');
        if (!historyList) return;

        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div>${text}</div>
            <div class="history-date">${new Date().toLocaleString()}</div>
        `;
        historyList.insertBefore(item, historyList.firstChild);

        // Сохраняем в БД
        this.userData.history = this.userData.history || [];
        this.userData.history.unshift({
            text,
            date: new Date().toISOString()
        });

        // Ограничиваем историю 50 записями
        if (this.userData.history.length > 50) {
            this.userData.history.pop();
        }
    }

    loadHistory() {
        const historyList = document.querySelector('.history-list');
        if (!historyList || !this.userData.history) return;

        this.userData.history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <div>${item.text}</div>
                <div class="history-date">${new Date(item.date).toLocaleString()}</div>
            `;
            historyList.appendChild(div);
        });
    }

    startPassiveIncome() {
        setInterval(() => {
            if (this.passiveIncome > 0) {
                this.stars += this.passiveIncome * this.x2Multiplier;
                totalStars += this.passiveIncome * this.x2Multiplier;
                this.updateMainUI();
                this.saveUserData();
            }
        }, 1000);
    }

    startEnergyRegeneration() {
        setInterval(() => {
            if (this.energy < this.maxEnergy) {
                this.energy = Math.min(this.energy + 1, this.maxEnergy);
                this.updateMainUI();
            }
        }, 3000);
    }

    checkX2Bonus() {
        setInterval(() => {
            if (!this.x2EndTime || Date.now() > this.x2EndTime) {
                // Запускаем новый x2 бонус
                this.x2Multiplier = 2;
                this.x2EndTime = Date.now() + 2 * 60 * 1000; // 2 минуты

                setTimeout(() => {
                    this.x2Multiplier = 1;
                    this.x2EndTime = null;
                }, 2 * 60 * 1000);
            }
        }, 10 * 60 * 1000); // Каждые 10 минут
    }

    getTodayDate() {
        return new Date().toISOString().split('T')[0];
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 3000);
    }

    saveUserData() {
        // Обновляем данные пользователя
        this.userData.stars = this.stars;
        this.userData.tapPower = this.tapPower;
        this.userData.maxEnergy = this.maxEnergy;
        this.userData.passiveIncome = this.passiveIncome;
        this.userData.totalClicks = this.totalClicks;
        userData.todayClicks = todayClicks;
        userData.todayStars = todayStars;
        userData.totalStars = totalStars;

        // Сохраняем в БД
        Database.saveUserData(this.userData);
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    window.app = new StellarClicker();
});