document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/profile') {
        loadProfileData();
    }
});

function loadProfileData() {
    const profileContainer = document.getElementById('profile-data');
    if (!profileContainer) return;
    
    profileContainer.innerHTML = '<div class="loading">Загрузка данных...</div>';
    
    fetch('/api/get_user_data')
    .then(response => {
        if (response.status === 401) {
            window.location.href = '/auth_redirect';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data?.status === 'success') {
            renderProfile(data.data);
        } else {
            showError(data?.message || 'Ошибка загрузки данных');
        }
    })
    .catch(error => {
        showError('Ошибка соединения');
        console.error('Profile load error:', error);
    });
}

function renderProfile(data) {
    const profileContainer = document.getElementById('profile-data');
    if (!profileContainer) return;
    
    profileContainer.innerHTML = `
        <div class="profile-header">
            <img src="{{ url_for('static', filename='images/user-placeholder.png') }}" alt="Аватар" class="avatar">
            <h2>${data.user.first_name} ${data.user.last_name || ''}</h2>
            <p class="username">@${data.user.username || 'нет username'}</p>
        </div>
        <div class="profile-details">
            <div class="detail">
                <span>ID:</span>
                <strong>${data.user.user_id}</strong>
            </div>
            <div class="detail">
                <span>Язык:</span>
                <strong>${data.user.language_code || 'не указан'}</strong>
            </div>
            <div class="balance">
                <span>Баланс:</span>
                <strong>${data.balance} ₽</strong>
            </div>
        </div>
    `;
}

function showError(message) {
    const profileContainer = document.getElementById('profile-data');
    if (profileContainer) {
        profileContainer.innerHTML = `<div class="error">${message}</div>`;
    }
}