const tg = window.Telegram.WebApp;
let tonConnectUI;

function showStatus(type, message) {
  const statusElement = document.getElementById('status');
  statusElement.style.display = 'block';
  statusElement.className = `status ${type}`;
  statusElement.textContent = message;
}

function isTelegramWebApp() {
  return typeof Telegram !== 'undefined' &&
         typeof Telegram.WebApp !== 'undefined';
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

function setupTonWallet() {
  try {
    if (!window.TON_CONNECT_UI || !document.getElementById('connect-btn')) {
      throw new Error('TON Connect not available');
    }

    tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
      manifestUrl: 'https://mitcoin.ru/tonconnect-manifest.json',
      buttonRootId: 'connect-btn',
      uiPreferences: { 
        language: 'ru'
      }
    });

    // Установка URL для перенаправления после подключения
    tonConnectUI.uiOptions = {
      twaReturnUrl: 'https://t.me/mitcoin2bot/app'
    };

    tonConnectUI.onStatusChange(wallet => {
      console.log('Wallet status changed:', wallet);
      // Здесь можно добавить логику при изменении статуса кошелька
    });
    
  } catch (error) {
    console.error('TON Connect error:', error);
    showStatus('error', 'Ошибка подключения TON кошелька');
  }
}

async function initApp() {
  try {
    if (!isTelegramWebApp()) {
      throw new Error("Приложение работает только в Telegram");
    }
    
    // Показываем контент ДО загрузки конфига
    document.getElementById('app-content').classList.remove('hidden');
    document.getElementById('footer-menu').classList.remove('hidden');
    document.getElementById('telegram-only-message').classList.add('hidden');
    
    tg.expand();
    setupNavigation();
    setupTonWallet();
    console.log('TON_CONNECT_UI:', window.TON_CONNECT_UI);
    console.log('connect-btn:', document.getElementById('connect-btn'));

    
    const user = tg.initDataUnsafe.user;
    if (!user?.id) {
      throw new Error("ID пользователя не найден");
    }
    
    window.userData = user;
    
  } catch (error) {
    console.error('Ошибка инициализации:', error);
    document.getElementById('telegram-only-message').classList.remove('hidden');
    showStatus('error', `❌ ${error.message}`);
  }
}

document.addEventListener('DOMContentLoaded', initApp);

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp(); // если DOM уже загружен
}