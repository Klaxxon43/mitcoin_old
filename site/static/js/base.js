const tg = window.Telegram.WebApp;

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

function initApp() {
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
