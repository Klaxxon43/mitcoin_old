// Общие функции для всего приложения
const tg = window.Telegram.WebApp;
let tonConnectUI;

function showStatus(type, message) {
  const statusElement = document.getElementById('status');
  statusElement.style.display = 'block';
  statusElement.className = `status ${type}`;
  statusElement.textContent = message;
}

function isTelegramWebApp() {
  try {
    return window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData;
  } catch (e) {
    return false;
  }
}

function setupNavigation() {
  const menuItems = document.querySelectorAll('.menu-item');
  
  menuItems.forEach(item => {
    item.addEventListener('click', function() {
      const route = this.getAttribute('data-route');
      if (window.location.pathname !== route) {
        window.location.href = route;
      }
    });
  });
}

function setupHeader(user) {
  if (!user) return;
  
  // Устанавливаем аватар
  const avatar = document.getElementById('user-avatar');
  if (user.photo_url) {
    avatar.src = user.photo_url;
  } else {
    avatar.src = 'https://cdn-icons-png.flaticon.com/512/149/149071.png';
  }
  
  // Устанавливаем имя
  const userName = document.getElementById('user-name');
  let name = user.first_name || '';
  if (user.last_name) name += ' ' + user.last_name;
  if (!name.trim() && user.username) name = '@' + user.username;
  userName.textContent = name.trim() || 'Пользователь';
  
  // Настраиваем кнопку TON кошелька в шапке
  tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
    manifestUrl: 'https://mitcoin.ru/tonconnect-manifest.json',
    buttonRootId: 'header-ton-connect',
    uiOptions: {
      twaReturnUrl: 'https://t.me/mitcoin2bot',
      buttonTheme: 'light',
      buttonSize: 'small'
    }
  });
}

async function initApp() {
  try {
    if (!isTelegramWebApp()) {
      throw new Error("Приложение работает только в Telegram");
    }
    
    // Инициализация интерфейса
    document.getElementById('app-header').classList.remove('hidden');
    document.getElementById('app-content').classList.remove('hidden');
    document.getElementById('footer-menu').classList.remove('hidden');
    document.getElementById('telegram-only-message').classList.add('hidden');
    
    tg.expand();
    setupNavigation();
    
    // Получаем данные пользователя из Telegram WebApp
    const user = tg.initDataUnsafe.user;
    if (!user?.id) {
      throw new Error("ID пользователя не найден");
    }
    
    // Настраиваем шапку
    setupHeader(user);
    
    // Сохраняем данные пользователя для использования в других скриптах
    window.userData = user;
    
  } catch (error) {
    console.error('Ошибка инициализации:', error);
    document.getElementById('telegram-only-message').classList.remove('hidden');
    showStatus('error', `❌ ${error.message}`);
  }
}

// Запуск приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', initApp);