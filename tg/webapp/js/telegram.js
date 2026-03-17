// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;

// Расширяем на весь экран
tg.expand();

// Делаем кнопку "Назад" невидимой (мы используем свою навигацию)
tg.BackButton.hide();

// Получаем данные пользователя
const user = tg.initDataUnsafe?.user;

// Отправляем данные в бота
function sendDataToBot(data) {
    tg.sendData(JSON.stringify(data));
}

// Готовность приложения
tg.ready();