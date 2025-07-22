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

async function authorize() {
  try {
    const response = await fetch('/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: tg.initData })
    });
    
    if (!response.ok) {
      throw new Error(await response.text());
    }
    
    return await response.json();
  } catch (error) {
    console.error('Auth error:', error);
    showStatus('error', `❌ Ошибка авторизации: ${error.message}`);
    throw error;
  }
}

async function loadUserData(userId) {
  try {
    const response = await fetch('/get_user_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    
    if (!response.ok) {
      throw new Error(await response.text());
    }
    
    const data = await response.json();
    if (data.status !== 'success') {
      throw new Error(data.message || 'Не удалось загрузить данные пользователя');
    }
    
    return data.user;
  } catch (error) {
    console.error('Ошибка загрузки данных пользователя:', error);
    showStatus('error', `❌ ${error.message}`);
    throw error;
  }
}

function updateWelcomeMessage(user) {
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || 
              (user.username ? `@${user.username}` : 'Пользователь');
  document.getElementById('welcome-text').textContent = `Привет, ${name.trim()}!`;
}

function displayUserData(userData) {
  const name = [userData.first_name, userData.last_name].filter(Boolean).join(' ') || 
              (userData.username ? `@${userData.username}` : 'Пользователь');
  
  document.getElementById('user-data').innerHTML = `
    <p><strong>🆔 ID:</strong> ${userData.user_id}</p>
    <p><strong>👤 Имя:</strong> ${name}</p>
    <p><strong>🔗 Имя пользователя:</strong> @${userData.username || 'N/A'}</p>
    <p><strong>🌐 Язык:</strong> ${userData.language_code || 'N/A'}</p>
  `;
  
  document.getElementById('balance').textContent = `${userData.balance || 0} ₽`;
  showStatus('success', '✅ Профиль успешно загружен');
}

function setupTonWallet() {
  tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
    manifestUrl: 'https://mitcoin.ru/tonconnect%E2%80%91manifest.json',
    buttonRootId: 'ton-connect',
    uiOptions: {
      twaReturnUrl: 'https://t.me/mitcoin2bot'
    }
  });

  tonConnectUI.connectionRestored.then(() => {
    const walletConnectionSource = {
      jsBridgeKey: 'tonconnect'
    };
    
    tonConnectUI.connect(walletConnectionSource).then(() => {
      updateWalletInfo();
    });
  });

  tonConnectUI.onStatusChange((wallet) => {
    if (wallet) {
      updateWalletInfo();
      showStatus('success', 'TON кошелек успешно подключен');
    } else {
      document.getElementById('wallet-info').style.display = 'none';
      showStatus('info', 'TON кошелек отключен');
    }
  });
}

async function updateWalletInfo() {
  const wallet = tonConnectUI.wallet;
  if (!wallet) {
    document.getElementById('wallet-info').style.display = 'none';
    return;
  }

  try {
    const address = wallet.account.address;
    document.getElementById('wallet-info').style.display = 'block';
    
    const res = await fetch(`https://tonapi.io/v2/accounts/${address}`);
    const json = await res.json();
    document.getElementById('wallet-balance').textContent = (parseInt(json.balance) / 1e9).toFixed(6);
  } catch (error) {
    console.error('Ошибка получения данных кошелька:', error);
    document.getElementById('wallet-balance').textContent = 'Ошибка';
    showStatus('error', 'Не удалось получить данные кошелька');
  }
}

async function initApp() {
  try {
    if (!isTelegramWebApp()) {
      throw new Error("Приложение работает только в Telegram");
    }
    
    document.getElementById('app-content').classList.remove('hidden');
    document.getElementById('telegram-only-message').classList.add('hidden');
    document.getElementById('footer-menu').classList.remove('hidden');
    
    tg.expand();
    setupNavigation();
    
    await authorize();
    
    const user = tg.initDataUnsafe.user;
    if (!user?.id) {
      throw new Error("ID пользователя не найден");
    }
    
    const userData = await loadUserData(user.id);
    window.userData = userData; // Сохраняем данные пользователя в глобальной области
    
  } catch (error) {
    console.error('Ошибка инициализации:', error);
    document.getElementById('telegram-only-message').classList.remove('hidden');
    showStatus('error', `❌ ${error.message}`);
  }
}