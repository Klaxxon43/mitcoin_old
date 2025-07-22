document.addEventListener('DOMContentLoaded', async () => {
    try {
        const user = await fetchUserData();  // 🔽 получаем с сервера
        displayUserData(user);
        setupTonWallet();
    } catch (err) {
        console.error(err);
        showStatus('error', '❌ Ошибка загрузки профиля');
    }
});

async function fetchUserData() {
    const response = await fetch('/me'); // авторизованный маршрут
    if (!response.ok) throw new Error('Ошибка получения данных профиля');
    const data = await response.json();
    if (data.status !== 'success') throw new Error(data.message || 'Ошибка профиля');
    return data.user;
}

document.addEventListener('DOMContentLoaded', () => {
    if (!window.userData) return;
    
    // Заполняем данные профиля
    displayUserData(window.userData);
    
    // Инициализация TON кошелька
    setupTonWallet();
});

function displayUserData(user) {
    const userDataElement = document.getElementById('user-data');
    const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || 
                (user.username ? `@${user.username}` : 'Пользователь');
    
    userDataElement.innerHTML = `
        <p><strong>🆔 ID:</strong> ${user.id || user.user_id || 'N/A'}</p>
        <p><strong>👤 Имя:</strong> ${name}</p>
        <p><strong>🔗 Имя пользователя:</strong> @${user.username || 'не_установлен'}</p>
        <p><strong>🌐 Язык:</strong> ${user.language_code || 'Не определен'}</p>
    `;
    
    // Обновляем баланс
    updateUserBalance(user);
}

async function updateUserBalance(user) {
    const balanceElement = document.getElementById('balance');
    
    // Если баланс есть в данных пользователя
    if (user.balance !== undefined) {
        balanceElement.textContent = `${user.balance.toLocaleString('ru-RU')} ₽`;
        return;
    }
    
    // Если баланса нет, запрашиваем с сервера
    try {
        const userId = user.id || user.user_id;
        if (!userId) {
            throw new Error('ID пользователя не найден');
        }
        
        const response = await fetch('/get_user_balance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка сервера');
        }
        
        const data = await response.json();
        if (data.status !== 'success') {
            throw new Error(data.message || 'Не удалось получить баланс');
        }
        
        balanceElement.textContent = `${data.balance.toLocaleString('ru-RU')} ₽`;
    } catch (error) {
        console.error('Ошибка получения баланса:', error);
        balanceElement.textContent = 'Ошибка загрузки';
        showStatus('error', 'Не удалось загрузить баланс');
    }
}

function setupTonWallet() {
    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: 'https://mitcoin.ru/tonconnect-manifest.json',
        buttonRootId: 'ton-connect',
        uiOptions: {
            twaReturnUrl: 'https://t.me/mitcoin2bot',
            buttonTheme: 'dark',
            buttonSize: 'medium'
        }
    });

    tonConnectUI.onStatusChange((wallet) => {
        const walletInfo = document.getElementById('wallet-info');
        if (wallet) {
            walletInfo.style.display = 'block';
            updateWalletBalance(wallet.account.address);
        } else {
            walletInfo.style.display = 'none';
        }
    });
}

async function updateWalletBalance(address) {
    try {
        const response = await fetch(`https://tonapi.io/v2/accounts/${address}`);
        if (!response.ok) {
            throw new Error('Ошибка запроса к TonAPI');
        }
        
        const data = await response.json();
        const balance = (parseInt(data.balance) / 1e9).toFixed(2);
        document.getElementById('wallet-balance').textContent = balance;
    } catch (error) {
        console.error('Ошибка получения баланса TON:', error);
        document.getElementById('wallet-balance').textContent = 'Ошибка';
        showStatus('error', 'Не удалось получить баланс TON кошелька');
    }
}

function showStatus(type, message) {
    const statusElement = document.getElementById('status');
    statusElement.style.display = 'block';
    statusElement.className = `status ${type}`;
    statusElement.textContent = message;
}