// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;

// Расширяем на весь экран
tg.expand();

// Настраиваем основную кнопку (если нужно)
tg.MainButton.setText('Закрыть');
tg.MainButton.onClick(() => tg.close());

// Получаем данные пользователя
const user = tg.initDataUnsafe?.user;

if (user) {
    console.log('Пользователь:', user);
}

// Готовность приложения
tg.ready();