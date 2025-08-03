let appConfig = {}; // Глобальный объект конфига
let miningInterval;
let currentEarnings = 0;
let currentMinedTime = 0;
let tonConnectUI;
let miningPurchaseTransaction = null;

// Функции для работы с UI
function showStatus(type, message) {
  const statusElement = document.getElementById('status');
  if (!statusElement) return;
  
  statusElement.style.display = 'block';
  statusElement.className = `status ${type}`;
  statusElement.textContent = message;
}

function setupMiningAutoRefresh() {
  // Очищаем предыдущий интервал, если он был
  if (miningInterval) {
    clearInterval(miningInterval);
  }
  
  // Устанавливаем новый интервал обновления (каждые 30 секунд)
  miningInterval = setInterval(async () => {
    try {
      await showMiningStatus();
    } catch (error) {
      console.error('Auto-refresh error:', error);
    }
  }, 30000); // 30 секунд
}

// Добавляем обработчик события для кнопки обновления
function setupRefreshButton() {
  const refreshButton = document.getElementById('refresh-button');
  if (refreshButton) {
    refreshButton.addEventListener('click', async () => {
      try {
        await showMiningStatus();
      } catch (error) {
        console.error('Refresh error:', error);
        showStatus('error', 'Ошибка при обновлении');
      } 
    });
  }
}

function updateWelcomeMessage(user) {
  const welcomeElement = document.getElementById('welcome-text');
  if (!welcomeElement) return;

  let name = "User";
  if (user) {
    if (user.first_name) name = user.first_name;
    if (user.last_name) name += " " + user.last_name;
    if (user.username && !user.first_name) name = "@" + user.username;
  }
  welcomeElement.textContent = `Привет, ${name.trim()}!`;
}

function setupNavigation() {
  const menuItems = document.querySelectorAll('.menu-item');
  
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

// Функции для работы с конфигом
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

// Функции для работы с Telegram WebApp
function isTelegramWebApp() {
  return typeof Telegram !== 'undefined' &&
         typeof Telegram.WebApp !== 'undefined';
}



function getUserId() {
  if (appConfig.DEBUG_MODE && appConfig.DEV_USER_ID) {
    return appConfig.DEV_USER_ID;
  }
  
  if (isTelegramWebApp()) {
    return Telegram.WebApp.initDataUnsafe.user?.id;
  }
  
  return null;
}

// Функции для работы с майнингом
function createConfetti(container) {
  const colors = ['#6e45e2', '#88d3ce', '#ff9a9e', '#fad0c4', '#a18cd1'];
  for (let i = 0; i < 50; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confetti.style.left = Math.random() * 100 + '%';
    confetti.style.top = '100%';
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.width = Math.random() * 8 + 6 + 'px';
    confetti.style.height = confetti.style.width;
    confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
    container.appendChild(confetti);
    
    setTimeout(() => {
      confetti.style.animation = `confetti ${Math.random() * 3 + 2}s forwards`;
      confetti.style.opacity = '1';
    }, 10);
    
    setTimeout(() => {
      confetti.remove();
    }, 5000);
  }
}

function parseTimeToSeconds(str) {
  let totalSeconds = 0;
  const dayMatch = str.match(/(\d+)\s*д/);
  const hourMatch = str.match(/(\d+)\s*ч/);
  const minuteMatch = str.match(/(\d+)\s*м/);
  const secondMatch = str.match(/(\d+)\s*с/);

  if (dayMatch) totalSeconds += parseInt(dayMatch[1]) * 86400;
  if (hourMatch) totalSeconds += parseInt(hourMatch[1]) * 3600;
  if (minuteMatch) totalSeconds += parseInt(minuteMatch[1]) * 60;
  if (secondMatch) totalSeconds += parseInt(secondMatch[1]);
  return totalSeconds;
}

function formatTime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  let result = '';
  if (days > 0) result += `${days}д `;
  if (hours > 0) result += `${hours}ч `;
  if (minutes > 0) result += `${minutes}м `;
  if (secs > 0 && days === 0) result += `${secs}с`;
  
  return result.trim() || '0с';
}

async function showMiningStatus() {
  const miningContainer = document.getElementById('mining-container');
  if (!miningContainer) return;

  try {
    // Показываем индикатор загрузки
    miningContainer.innerHTML = `
      <div class="loading-animation">
        <div class="loading-spinner"></div>
        <div class="loading-text">Загрузка данных...</div>
      </div>
    `;

    const userId = getUserId();
    
    if (!userId) {
      miningContainer.innerHTML = `
        <div style="text-align: center; padding: 40px 20px;">
          <h3 style="color: #88d3ce;">Приложение работает только в Telegram</h3>
          <p style="color: #aaa;">Откройте это приложение через Telegram Mini App</p>
        </div>
      `;
      return;
    }

    // Подготавливаем параметры запроса
    const requestOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId })
    };

    // В режиме разработки добавляем специальный заголовок
    if (appConfig.DEBUG_MODE) {
      requestOptions.headers['X-Dev-User-Id'] = appConfig.DEV_USER_ID;
    }
    // В Telegram WebApp добавляем initData
    else if (isTelegramWebApp()) {
      requestOptions.headers['X-Telegram-InitData'] = Telegram.WebApp.initData;
    }

    const response = await fetch('/mining/status', requestOptions);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(error.message || `Server error: ${response.status}`);
    }

    const miningData = await response.json();
    renderMiningStatus(miningContainer, miningData, userId);

  } catch (error) {
    console.error('Mining status error:', error);
    miningContainer.innerHTML = `
      <div style="color: #ff6b6b; text-align: center; margin-top: 50px;">
        Ошибка: ${error.message}
      </div>
    `;
  }
}

function renderMiningStatus(container, data, userId) {
  container.innerHTML = '';

  if (data.is_active) {
    renderActiveMining(container, data, userId);
  } else {
    renderInactiveMining(container, data, userId);
  }
}

function renderActiveMining(container, data, userId) {
  const template = document.getElementById('active-mining-template');
  const clone = template.content.cloneNode(true);
  
  const currentEarnings = Number(data.earnings) || 0;
  const currentMinedTime = parseTimeToSeconds(data.mined_time || "0с");
  
  // Обновляем значения в интерфейсе
  const miningAmount = clone.querySelector('.mining-amount');
  if (miningAmount) miningAmount.textContent = currentEarnings.toFixed(2);
  
  const progressFilled = clone.querySelector('.progress-filled');
  if (progressFilled) {
    const timeLeft = data.time_left || 120;
    const progressPercent = ((120 - timeLeft) / 120) * 100;
    progressFilled.style.width = `${progressPercent}%`;
    
    miningAmount.style.left = progressPercent < 100 ? 
      `${progressPercent}%` : '50%';
    miningAmount.style.transform = 'translateX(-50%)';
  }
  
  const minedTimeValue = clone.querySelector('.mined-time-value');
  if (minedTimeValue) minedTimeValue.textContent = formatTime(currentMinedTime);
  
  const coinsValue = clone.querySelector('.coins-value');
  if (coinsValue) coinsValue.textContent = currentEarnings.toFixed(2);
  
  // Настраиваем кнопку сбора
  const collectButton = clone.querySelector('.collect-button');
  if (collectButton) {
    collectButton.addEventListener('click', () => handleCollect(userId, container));
    
    if (data.can_collect) {
      collectButton.classList.add('pulse');
    } else {
      collectButton.disabled = true;
      const timeToCollect = 300 - currentMinedTime;
      collectButton.textContent = `До сбора: ${formatTime(timeToCollect)}`;
    }
  }
  
  if (data.time_left <= 0) {
    container.classList.add('completed-animation');
  } else {
    container.classList.remove('completed-animation');
  }
  
  container.appendChild(clone);
}

function renderInactiveMining(container, data, userId) {
  const template = document.getElementById('inactive-mining-template');
  const clone = template.content.cloneNode(true);
  
  const buyButton = clone.querySelector('.buy-button');
  if (buyButton) {
    buyButton.addEventListener('click', () => handleStartMining(userId, container));
  }
  
  container.appendChild(clone);
}

async function handleCollect(userId, container) {
  try {
    const collectButton = container.querySelector('.collect-button');
    if (collectButton) {
      collectButton.disabled = true;
      collectButton.textContent = 'Подготовка...';
    }

    // Показываем рекламу перед сбором
    await showRewardedAd();

    // Продолжаем процесс сбора после просмотра рекламы
    if (collectButton) {
      collectButton.textContent = 'Сбор...';
    }

    const requestOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId })
    };

    if (appConfig.DEBUG_MODE) {
      requestOptions.headers['X-Dev-User-Id'] = appConfig.DEV_USER_ID;
    } else if (isTelegramWebApp()) {
      requestOptions.headers['X-Telegram-InitData'] = Telegram.WebApp.initData;
    }

    const response = await fetch('/mining/collect', requestOptions);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Collection failed' }));
      throw new Error(error.message);
    }

    createConfetti(container);
    setTimeout(() => showMiningStatus(), 1500);
    
  } catch (error) {
    console.error('Collect error:', error);
    const collectButton = container.querySelector('.collect-button');
    if (collectButton) {
      collectButton.disabled = false;
      collectButton.textContent = 'Собрать';
    }
    showStatus('error', `Ошибка: ${error.message}`);
  }
}

async function showRewardedAd() {
  return new Promise((resolve, reject) => {
    showStatus('info', 'Загрузка рекламы...');
    
    window.Sonar.show({ 
      adUnit: 'rewarded',
      loader: true,
      
      onStart: () => {
        console.log('Реклама начала загружаться');
      },
      
      onShow: () => {
        showStatus('info', 'Смотрите рекламу для получения награды');
      },
      
      onError: (error) => {
        showStatus('error', 'Ошибка загрузки рекламы');
        reject(new Error(error?.message || 'Ошибка при показе рекламы'));
      },
      
      onClose: () => {
        console.log('Реклама закрыта');
      },
      
      onReward: () => {
        showStatus('success', 'Реклама просмотрена!');
        resolve({ status: 'completed' });
      }
    }).then((result) => {
      if (result.status === 'error') {
        reject(new Error(result.message || 'Ошибка при показе рекламы'));
      }
    }).catch(reject);
  });
}

async function handleStartMining(userId, container) {
  try {
    const buyButton = container.querySelector('.buy-button');
    if (buyButton) {
      buyButton.disabled = true;
      buyButton.textContent = 'Подготовка...';
    }

    // Проверяем, подключен ли кошелек
    if (!tonConnectUI || !tonConnectUI.connected) {
      throw new Error('Сначала подключите кошелек');
    }

    // Создаем транзакцию для оплаты 0.01 TON
    const transaction = {
      validUntil: Math.floor(Date.now() / 1000) + 300, // 5 минут
      messages: [
        {
          // Адрес для оплаты (замените на реальный адрес вашего контракта)
          address: "EQABa48hjKzg09hN_HjxOic7r8T1PleIy1dRd8NvZ3922MP0",
          amount: "10000000", // 0.01 TON в нанотонах
          payload: "Оплата майнинг контракта" // Комментарий к платежу
        }
      ]
    };

    // Показываем модальное окно с подтверждением платежа
    buyButton.textContent = 'Подтвердите платеж...';
    const result = await tonConnectUI.sendTransaction(transaction);
    
    // Сохраняем данные транзакции для проверки
    miningPurchaseTransaction = {
      boc: result.boc,
      userId: userId,
      container: container
    };

    // Показываем статус ожидания подтверждения
    buyButton.textContent = 'Ожидаем подтверждения...';
    showStatus('info', 'Платеж отправлен, ожидаем подтверждения...');

    // Запускаем проверку статуса транзакции
    setTimeout(() => checkMiningPurchaseStatus(), 5000);

  } catch (error) {
    console.error('Mining purchase error:', error);
    const buyButton = container.querySelector('.buy-button');
    if (buyButton) {
      buyButton.disabled = false;
      buyButton.textContent = 'Активировать майнинг';
    }
    showStatus('error', `Ошибка: ${error.message}`);
  }
} 

// Функция проверки статуса покупки
async function checkMiningPurchaseStatus() {
  if (!miningPurchaseTransaction) return;

  try {
    const { boc, userId, container } = miningPurchaseTransaction;
    
    // Отправляем запрос на сервер для проверки транзакции
    const requestOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: userId,
        transaction_boc: boc
      })
    };

    if (appConfig.DEBUG_MODE) {
      requestOptions.headers['X-Dev-User-Id'] = appConfig.DEV_USER_ID;
    } else if (isTelegramWebApp()) {
      requestOptions.headers['X-Telegram-InitData'] = Telegram.WebApp.initData;
    }

    const response = await fetch('/mining/verify_payment', requestOptions);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Payment verification failed' }));
      throw new Error(error.message);
    }

    const result = await response.json();
    
    if (result.status === 'confirmed') {
      // Платеж подтвержден, активируем майнинг
      showStatus('success', 'Платеж подтвержден! Активируем майнинг...');
      createConfetti(container);
      setTimeout(() => showMiningStatus(), 1500);
      miningPurchaseTransaction = null;
    } else if (result.status === 'pending') {
      // Платеж еще не подтвержден, проверяем снова через 5 секунд
      showStatus('info', 'Платеж еще не подтвержден, проверяем снова...');
      setTimeout(() => checkMiningPurchaseStatus(), 5000);
    } else {
      throw new Error(result.message || 'Неизвестный статус платежа');
    }

  } catch (error) {
    console.error('Payment verification error:', error);
    showStatus('error', `Ошибка проверки платежа: ${error.message}`);
    
    const buyButton = document.querySelector('.buy-button');
    if (buyButton) {
      buyButton.disabled = false;
      buyButton.textContent = 'Попробовать снова';
    }
    
    // Через 30 секунд сбрасываем состояние
    setTimeout(() => {
      miningPurchaseTransaction = null;
      showMiningStatus();
    }, 30000);
  }
}

// Обновляем функцию renderInactiveMining
function renderInactiveMining(container, data, userId) {
  container.innerHTML = '';

  const inactiveTemplate = document.createElement('div');
  inactiveTemplate.className = 'mining-inactive';
  inactiveTemplate.innerHTML = `
    <div class="mining-card">
      <h3>Майнинг не активен</h3>
      <p>Для активации майнинга необходимо внести депозит 0.01 TON</p>
      <div class="mining-price">
        <span class="price-amount">0.01</span>
        <span class="price-currency">TON</span>
      </div>
      <button class="buy-button">Активировать майнинг</button>
      <p class="info-text">После активации вы начнете получать $MICO каждые 5 минут</p>
    </div>
  `;

  const buyButton = inactiveTemplate.querySelector('.buy-button');
  if (buyButton) {
    buyButton.addEventListener('click', () => handleStartMining(userId, container));
  }

  container.appendChild(inactiveTemplate);
}

// Основная функция инициализации
async function initApp() {
  try {
    await loadConfig();
    if (appConfig.DEBUG_MODE) {
      console.log('Auto-refresh initialized');
    }

    if (appConfig.DEBUG_MODE) {
      const banner = document.getElementById('dev-mode-banner');
      if (banner) banner.classList.remove('hidden');
    }

    document.getElementById('app-content').classList.remove('hidden');
    document.getElementById('footer-menu').classList.remove('hidden');

    const userId = getUserId();
    if (!userId) {
      throw new Error("Не удалось определить ID пользователя");
    }

    const response = await fetch(`/get_user_balance?user_id=${userId}`);
    const balanceData = await response.json();

    const user = {
      user_id: userId,
      first_name: appConfig.DEBUG_MODE ? null : Telegram?.WebApp?.initDataUnsafe?.user?.first_name,
      last_name: appConfig.DEBUG_MODE ? null : Telegram?.WebApp?.initDataUnsafe?.user?.last_name,
      username: appConfig.DEBUG_MODE ? null : Telegram?.WebApp?.initDataUnsafe?.user?.username,
      balance: balanceData.balance || 0
    };

    updateWelcomeMessage(user);
    setupNavigation();
    setupRefreshButton();
    await showMiningStatus();
    
    showStatus('success', appConfig.DEBUG_MODE ? 
      'Development mode active' : 'Successfully initialized');
  } catch (error) {
    console.error('Init error:', error);
    
    if (appConfig.DEBUG_MODE) {
      const balanceResponse = await fetch(`/get_user_balance?user_id=${appConfig.DEV_USER_ID}`);
      const balanceData = await balanceResponse.json();
      
      updateWelcomeMessage({
        user_id: appConfig.DEV_USER_ID,
        balance: balanceData.balance || 0
      });
      setupMiningAutoRefresh();
      showStatus('error', `DEBUG MODE: Using fallback data (${error.message})`);
    } else if (!isTelegramWebApp()) {
      document.getElementById('telegram-only-message').classList.remove('hidden');
    } else {
      showStatus('error', error.message);
    }

    try {
      await showMiningStatus();
    } catch (e) {
      console.error('Failed to show mining status:', e);
    }
    setupMiningAutoRefresh();
  }
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', initApp);

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp(); // если DOM уже загружен
}

