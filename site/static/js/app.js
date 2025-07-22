// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем Telegram WebApp
    if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
        initTelegramApp();
    } else {
        handleNonTelegram();
    }
});

function initTelegramApp() {
    const tg = window.Telegram.WebApp;
    tg.expand();
    
    // Авторизуем пользователя
    const user = tg.initDataUnsafe.user;
    authorizeUser(user.id);
    
    // Настройка кнопки "Назад"
    if (tg.platform !== "unknown") {
        tg.BackButton.show();
        tg.BackButton.onClick(() => tg.close());
    }
}

function handleNonTelegram() {
    if (!window.location.pathname.includes('auth_redirect')) {
        window.location.href = '/auth_redirect';
    }
}

function authorizeUser(userId) {
    fetch('/api/auth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && window.location.pathname === '/auth_redirect') {
            window.location.href = '/';
        }
    })
    .catch(error => console.error('Auth error:', error));
}

// Активация кнопок в футере
function updateActiveButton() {
    const path = window.location.pathname;
    document.querySelectorAll('.footer-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (path === '/profile') {
        document.getElementById('profile-btn').classList.add('active');
    } else {
        document.getElementById('home-btn').classList.add('active');
    }
}

// Вызываем при загрузке и смене страниц
window.addEventListener('load', updateActiveButton);
window.addEventListener('popstate', updateActiveButton);