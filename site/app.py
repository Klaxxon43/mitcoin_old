from flask import Flask, request, jsonify, render_template, session
import requests
import time
import logging
from functools import wraps

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_API_URL = 'http://45.143.203.232:8000'
SECRET_KEY = 'your-secret-key-here'  # Замените на реальный секретный ключ

application = Flask(__name__)
application.secret_key = SECRET_KEY

def make_api_request(endpoint, data):
    """Универсальная функция для запросов к API"""
    for attempt in range(3):
        try:
            logger.info(f"Making API request to {endpoint} with data: {data}")
            response = requests.post(
                f"{BOT_API_URL}/{endpoint}",
                json=data,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"API response from {endpoint}: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {endpoint}: {str(e)}")
            if attempt == 2:
                raise
            time.sleep(1)

def telegram_auth_required(f):
    """Декоратор для проверки авторизации через Telegram"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authorized'):
            logger.warning("Unauthorized access attempt")
            return jsonify({"status": "error", "message": "Authorization required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@application.route("/")
def index():
    logger.info("Rendering home page")
    return render_template("home.html")

@application.route("/profile")
def profile():
    logger.info("Rendering profile page")
    return render_template("profile.html")

@application.route("/get_init_data", methods=["GET"])
def get_init_data():
    try:
        if not session.get('init_data'):
            return jsonify({"status": "error", "message": "Not authorized"}), 401
            
        return jsonify({
            "status": "success",
            "init_data": session['init_data']
        })
    except Exception as e:
        logger.error(f"Error in get_init_data: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
@application.route("/auth", methods=["POST"])
def auth():
    try:
        init_data = request.json.get('initData')
        if not init_data:
            logger.error("No initData provided")
            return jsonify({"status": "error", "message": "initData is required"}), 400

        # Здесь должна быть проверка подлинности initData через хэш
        # Для упрощения пропускаем, но в продакшене обязательно реализуйте
        # Пример: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

        # Сохраняем данные пользователя в сессии
        session['authorized'] = True
        session['init_data'] = init_data
        
        logger.info("User authorized successfully")
        return jsonify({"status": "success", "message": "Authorized successfully"})
        
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@application.route("/get_user_data", methods=["POST"])
@telegram_auth_required
def get_user_data():
    try:
        user_id = request.json.get('user_id')
        if not user_id:
            logger.error("No user_id provided")
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        try:
            logger.info(f"Fetching data for user {user_id}")
            
            # Получаем данные пользователя
            user_data = make_api_request("get_user", {"user_id": user_id})
            
            # Получаем баланс
            balance_data = make_api_request("get_balance", {"user_id": user_id})
            
            # Объединяем результаты
            response_data = {
                "status": "success",
                "user": {
                    **user_data,
                    "balance": balance_data.get("balance", 0)
                }
            }
            
            logger.info(f"Successfully fetched data for user {user_id}")
            return jsonify(response_data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for user {user_id}: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Failed to connect to API",
                "details": str(e)
            }), 502
            
    except Exception as e:
        logger.error(f"Unexpected error in get_user_data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@application.route("/logout", methods=["POST"])
def logout():
    session.clear()
    logger.info("User logged out")
    return jsonify({"status": "success", "message": "Logged out successfully"})

if __name__ == "__main__":
    try:
        logger.info("Starting application")
        application.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")