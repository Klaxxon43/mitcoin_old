class NotificationSystem {
    constructor() {
      // Создаем контейнер, если его нет
      this.container = document.getElementById('notification-container');
      if (!this.container) {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        document.body.appendChild(this.container);
      }
      this.setupSwipe();
      
      // Добавляем базовые стили, если CSS не подключен
      this.injectBaseStyles();
    }
  
    injectBaseStyles() {
      if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
          #notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            width: 300px;
            max-width: 90%;
            display: flex;
            flex-direction: column;
            gap: 10px;
          }
          .notification {
            position: relative;
            padding: 15px;
            border-radius: 8px;
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            transform: translateX(120%);
            transition: transform 0.3s ease-out;
            cursor: pointer;
            user-select: none;
          }
          .notification.show { transform: translateX(0); }
          .notification.hide { transform: translateX(120%); }
          .notification.success { background-color: #4CAF50; }
          .notification.error { background-color: #F44336; }
          .notification.warning { background-color: #FF9800; }
          .notification-content { margin-bottom: 10px; }
          .notification-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            background-color: rgba(255, 255, 255, 0.5);
            width: 100%;
            transform-origin: left;
            transform: scaleX(1);
          }
          @keyframes progress {
            from { transform: scaleX(1); }
            to { transform: scaleX(0); }
          }
          .notification-progress.active {
            animation: progress 3s linear forwards;
          }
        `;
        document.head.appendChild(style);
      }
    }
  
    show(type, message, duration = 3000) {
      if (!['success', 'error', 'warning'].includes(type)) {
        console.error('Invalid notification type:', type);
        return;
      }
  
      const notification = document.createElement('div');
      notification.className = `notification ${type}`;
      
      const content = document.createElement('div');
      content.className = 'notification-content';
      content.textContent = message;
      
      const progress = document.createElement('div');
      progress.className = 'notification-progress';
      
      notification.appendChild(content);
      notification.appendChild(progress);
      this.container.appendChild(notification);
      
      // Анимация появления
      setTimeout(() => notification.classList.add('show'), 10);
      
      // Анимация прогресса
      setTimeout(() => progress.classList.add('active'), 50);
      
      // Автоматическое закрытие
      const timer = setTimeout(() => {
        this.hide(notification);
      }, duration);
      
      // Обработчик клика
      notification.addEventListener('click', () => {
        clearTimeout(timer);
        this.hide(notification);
      });
      
      return notification;
    }
  
    hide(notification) {
      if (!notification) return;
      notification.classList.remove('show');
      notification.classList.add('hide');
      setTimeout(() => {
        if (notification.parentNode === this.container) {
          this.container.removeChild(notification);
        }
      }, 300);
    }
  
    setupSwipe() {
      let touchStartX = 0;
      
      this.container.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });
      
      this.container.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].screenX;
        if (touchEndX - touchStartX > 50) {
          const notification = e.target.closest('.notification');
          if (notification) {
            this.hide(notification);
          }
        }
      }, { passive: true });
    }
  }
  
// Создаем глобальный объект, даже если он уже существует (перезаписываем)
window.notificate = new NotificationSystem();

// Опционально: алиасы для удобства
window.Notify = window.notificate; // Можно использовать Notify.show()
  