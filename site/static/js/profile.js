let appConfig = {}; // Глобальный объект конфига
let tonConnectUI;

const elements = {
  appContent: document.getElementById('app-content'),
  telegramOnlyMessage: document.getElementById('telegram-only-message'),
  footerMenu: document.getElementById('footer-menu'),
  status: document.getElementById('status'),
  userData: document.getElementById('user-data'),
  balance: document.getElementById('balance'),
  tonBalance: document.getElementById('ton-balance'),
  walletInfo: document.getElementById('wallet-info'),
  devModeBanner: document.getElementById('dev-mode-banner'),
  connectBtn: document.getElementById('connect-btn'),
  showRewardedAdBtn: document.getElementById('show-rewarded-ad'),
  rewardedAdContainer: document.getElementById('rewarded')
};

async function loadConfig() {
  try {
    const response = await fetch('/get_config');
    if (!response.ok) throw new Error('Failed to load config');
    appConfig = await response.json();
    console.log('App config loaded:', appConfig);
  } catch (error) {
    console.error('Error loading config:', error);
    // Fallback значения
    appConfig = {
      DEBUG_MODE: false,
      DEV_USER_ID: 0
    };
  }
}

function showStatus(type, message) {
  if (!elements.status) return;
  elements.status.style.display = 'block';
  elements.status.className = `status ${type}`;
  elements.status.textContent = message;
}

function isTelegramWebApp() {
  return typeof Telegram !== 'undefined' &&
         typeof Telegram.WebApp !== 'undefined';
}


async function updateTonBalance(address) {
  try {
    const response = await fetch(`https://tonapi.io/v2/accounts/${address}`);
    const data = await response.json();
    const balance = (parseInt(data.balance) / 1e9).toFixed(2);
    elements.tonBalance.textContent = `${balance} TON`;
  } catch (error) {
    console.error('Error fetching TON balance:', error);
    elements.tonBalance.textContent = 'Error';
    showStatus('error', 'Failed to load TON balance');
  }
}

function setupNavigation() {
  const menuItems = document.querySelectorAll('.menu-item');
  if (!menuItems.length) return;

  menuItems.forEach(item => {
    item.addEventListener('click', function() {
      menuItems.forEach(i => i.classList.remove('active'));
      this.classList.add('active');
      const route = this.getAttribute('data-route');
      if (window.location.pathname !== route) {
        window.location.href = route;
      }
    });
  });
}

async function fetchUserBalance(userId) {
  try {
    let options = {};
    if (!appConfig.DEBUG_MODE && isTelegramWebApp()) {
      options.headers = {
        'X-Telegram-InitData': Telegram.WebApp.initData
      };
    }
    
    const response = await fetch(`/get_user_balance?user_id=${userId}`, options);
    if (!response.ok) throw new Error('Failed to fetch balance');
    const data = await response.json();
    return data.balance || 0;
  } catch (error) {
    console.error('Error fetching balance:', error);
    return 0;
  }
}

async function fetchUserData(userId) {
  try {
    const balance = await fetchUserBalance(userId);
    
    if (appConfig.DEBUG_MODE) {
      return {
        user_id: appConfig.DEV_USER_ID,
        first_name: null,
        last_name: null,
        username: null,
        language_code: null,
        balance: balance
      };
    }

    const tgUser = Telegram.WebApp.initDataUnsafe.user;
    if (!tgUser) throw new Error("Telegram user data not available");

    return {
      user_id: tgUser.id,
      first_name: tgUser.first_name,
      last_name: tgUser.last_name,
      username: tgUser.username,
      language_code: tgUser.language_code,
      balance: balance
    };
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
}

async function displayUserData(user) {
  if (!user || !elements.userData) {
    showStatus('error', 'User data not available');
    return;
  }

  try {
    const name = appConfig.DEBUG_MODE ? 'Dev User' : 
                [user.first_name, user.last_name].filter(Boolean).join(' ') || 
                (user.username ? `@${user.username}` : 'User');
    
    elements.userData.innerHTML = `
      <p><strong>🆔 ID:</strong> ${user.user_id || 'N/A'}</p>
      <p><strong>👤 Name:</strong> ${name}</p>
      <p><strong>🔗 Username:</strong> @${user.username || 'N/A'}</p>
    `; //       <p><strong>🌐 Language:</strong> ${user.language_code || 'N/A'}</p>
    
    elements.balance.textContent = `${user.balance.toFixed(2) || 0} $MICO`;
    // showStatus('success', '✅ Profile loaded successfully');
    notificate.show('success', 'Профиль успешно загружен');
    // Notification.show('success', 'Профиль успешно загружен')
  } catch (error) {
    console.error('Failed to display user data:', error);
    elements.userData.innerHTML = '<p>Error loading user data</p>';
    elements.balance.textContent = 'Error';
    showStatus('error', `❌ ${error.message}`);
  }
}

function setupTonWallet() {
  try {
    if (!window.TON_CONNECT_UI || !elements.connectBtn) {
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

    tonConnectUI.onStatusChange(async wallet => {
      if (!elements.walletInfo) return;

      if (wallet && wallet.account?.address) {
        elements.walletInfo.style.display = 'block';
        await updateTonBalance(wallet.account.address);
      } else {
        elements.walletInfo.style.display = 'none';
        elements.tonBalance.textContent = '–';
      }
    });
  } catch (error) {
    console.error('TON Connect error:', error);
    showStatus('error', 'TON wallet initialization failed');
  }
}

async function handleInitError(error) {
  console.error('Init error:', error);
  
  if (appConfig.DEBUG_MODE) {
    const balance = await fetchUserBalance(appConfig.DEV_USER_ID);
    const user = {
      user_id: appConfig.DEV_USER_ID,
      first_name: null,
      last_name: null,
      username: null,
      language_code: null,
      balance: balance
    };
    
    await displayUserData(user);
    showStatus('error', `DEBUG ERROR: ${error.message}`);
  } else if (!isTelegramWebApp() && elements.telegramOnlyMessage) {
    elements.telegramOnlyMessage.classList.remove('hidden');
  } else {
    showStatus('error', error.message);
  }
}

async function initApp() {
  // Загружаем конфиг первым делом
  await loadConfig();

  try {
    if (appConfig.DEBUG_MODE) {
      if (elements.devModeBanner) {
        elements.devModeBanner.classList.remove('hidden');
      }
    }

    console.log("isTelegramWebApp:", isTelegramWebApp());
    console.log("DEBUG_MODE:", appConfig.DEBUG_MODE);
    
    if (!isTelegramWebApp() && !appConfig.DEBUG_MODE) {
      console.log("Showing telegramOnlyMessage because not in Telegram and not in debug");
      if (elements.telegramOnlyMessage) {
        elements.telegramOnlyMessage.classList.remove('hidden');
      }
      throw new Error("Not in Telegram WebApp");
    }

    elements.appContent.classList.remove('hidden');
    elements.footerMenu.classList.remove('hidden');

    // Получаем данные пользователя
    const userId = appConfig.DEBUG_MODE ? appConfig.DEV_USER_ID : 
                  Telegram.WebApp.initDataUnsafe.user?.id;
    
    if (!userId) throw new Error("User ID not available");

    const user = await fetchUserData(userId);
    await displayUserData(user);
    setupTonWallet();
    setupNavigation();
    if (elements.showRewardedAdBtn) {
      elements.showRewardedAdBtn.addEventListener('click', showRewardedAd);
    }

  } catch (error) {
    await handleInitError(error);
  }
}

async function showRewardedAd() {
  return new Promise((resolve, reject) => {
    showStatus('info', 'Loading ad...');
    
    window.Sonar.show({ 
      adUnit: 'rewarded',
      loader: true,
      
      onStart: () => {
        console.log('Ad started loading');
      },
      
      onShow: () => {
        showStatus('info', 'Watch the ad to get reward');
      },
      
      onError: (error) => {
        showStatus('error', 'Ad loading error');
        reject(new Error(error?.message || 'Failed to show ad'));
      },
      
      onClose: () => {
        console.log('Ad closed');
        // Награда уже должна быть выдана в onReward, если пользователь заслужил её
      },
      
      onReward: () => {
        try {
          // Получаем userId
          const userId = appConfig.DEBUG_MODE ? appConfig.DEV_USER_ID : 
                       Telegram.WebApp.initDataUnsafe.user?.id;
          
          // Вызываем функцию начисления награды
          grantReward(userId);
          
          showStatus('success', 'Reward granted!');
          resolve({ status: 'completed' });
        } catch (error) {
          reject(error);
        }
      }
    }).then((result) => {
      if (result.status === 'error') {
        reject(new Error(result.message || 'Failed to show ad'));
      }
    }).catch(reject);
  });
}

// Функция для начисления награды
function grantReward(userId) {
  console.log('Reward granted for user:', userId);
  // Здесь должна быть логика начисления награды пользователю
  // Например, вызов API вашего сервера
}

async function sendTransaction() {
  if (!tonConnectUI.connected) {
    showStatus('error', 'Wallet is not connected');
    return;
  }

  try {
    const transaction = {
      validUntil: Math.floor(Date.now() / 1000) + 300, // 5 минут
      messages: [
        {
          address: "EQABa48hjKzg09hN_HjxOic7r8T1PleIy1dRd8NvZ3922MP0", // Адрес получателя
          amount: "20000000", // 0.02 TON в нанотонах. * 1000000000
          payload: "Тестовая транзакция" // Опциональное сообщение
        }
      ]
    };

    const result = await tonConnectUI.sendTransaction(transaction);
    console.log('Transaction sent:', result);
    showStatus('success', 'Transaction sent successfully!');
    
    // Можно отслеживать статус транзакции по result.boc
  } catch (error) {
    console.error('Transaction error:', error);
    showStatus('error', 'Failed to send transaction');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp(); // если DOM уже загружен
}