class StellarClicker {
    constructor() {
        this.currentPage = 'main';
        this.stars = 0;
        this.energy = 100;
        this.maxEnergy = 100;
        this.tapPower = 1;
        this.passiveIncome = 0;
        this.totalClicks = 0;
        this.todayClicks = 0;
        this.todayStars = 0;
        this.totalStars = 0;
        this.x2Multiplier = 1;
        this.energyRegen = true;

        this.init();
    }

    init() {
        // Загружаем главную страницу
        this.loadPage('main');

        // Навигация
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.switchPage(page);
            });
        });

        // Запускаем восстановление энергии
        this.startEnergyRegen();

        // Запускаем пассивный доход
        this.startPassiveIncome();
    }

    async loadPage(pageName) {
        try {
            const response = await fetch(`pages/${pageName}.html`);
            const html = await response.text();
            document.getElementById('content').innerHTML = html;
            this.currentPage = pageName;
            this.initPage(pageName);
        } catch (error) {
            console.error('Error loading page:', error);
        }
    }

    switchPage(page) {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });
        this.loadPage(page);
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
        // Обновляем счетчики
        this.updateMainUI();

        // Обработчик клика по звезде
        const clicker = document.getElementById('clickerImage');
        if (clicker) {
            clicker.addEventListener('click', (e) => {
                this.handleClick(e);
            });
        }
    }

    handleClick(e) {
        if (this.energy <= 0) {
            this.showEnergyWarning();
            return;
        }

        // Анимация
        e.target.classList.add('clicked');
        setTimeout(() => e.target.classList.remove('clicked'), 300);

        // Эффект звездочек
        this.createStarEffect(e);

        // Расчет награды
        const reward = this.tapPower * this.x2Multiplier;

        // Обновление статистики
        this.stars += reward;
        this.energy -= 2;
        this.totalClicks++;
        this.todayClicks++;
        this.todayStars += reward;
        this.totalStars += reward;

        // Обновление UI
        this.updateMainUI();

        // Отправка данных в бота
        this.sendDataToBot();
    }

    createStarEffect(e) {
        const container = document.getElementById('clickerEffects');
        if (!container) return;

        for (let i = 0; i < 5; i++) {
            const star = document.createElement('span');
            star.textContent = '⭐';
            star.style.position = 'absolute';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animation = 'float 1s ease-out';
            star.style.fontSize = '20px';
            star.style.pointerEvents = 'none';

            container.appendChild(star);

            setTimeout(() => star.remove(), 1000);
        }
    }

    updateMainUI() {
        const starsEl = document.getElementById('starsCounter');
        const energyText = document.getElementById('energyText');
        const energyBar = document.getElementById('energyBar