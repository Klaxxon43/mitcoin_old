document.addEventListener('DOMContentLoaded', async () => {
    try {
        const user = await fetchUserData();  // 🔽 получаем с сервера
        displayUserData(user);
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
