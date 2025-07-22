document.addEventListener('DOMContentLoaded', () => {
    if (!window.userData) return;
    
    // Обновляем приветственное сообщение
    const welcomeMessage = document.getElementById('welcome-message');
    let name = window.userData.first_name || '';
    if (window.userData.last_name) name += ' ' + window.userData.last_name;
    if (!name.trim() && window.userData.username) name = '@' + window.userData.username;
    welcomeMessage.textContent = `Привет, ${name.trim() || 'Пользователь'}! Рады видеть вас снова.`;
    
    // Обработчики для быстрых действий
    document.querySelectorAll('.action-item').forEach(item => {
      item.addEventListener('click', function() {
        const action = this.querySelector('span').textContent;
        showStatus('info', `Выбрано действие: ${action}`);
      });
    });
  });