from flask import Flask, request, jsonify, render_template, session
import requests
import time
import json
import logging
from functools import wraps
from urllib.parse import parse_qs, unquote
from config import DEBUG_MODE, DEV_USER_ID  # Импортируем из config.py

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

# Конфигурация
BOT_API_URL = 'http://45.143.203.232:8000'
SECRET_KEY = 'your-secret-key-here'  # Замените на реальный секретный ключ


application = Flask(__name__)
application.secret_key = SECRET_KEY

def make_api_request(endpoint, data):
    """
    Улучшенная версия с обработкой специфичных ошибок API
    """
    try:
        url = f"http://45.143.203.232:8000/{endpoint}"
        logger.info(f"API Request to {url} with data: {data}")
        
        response = requests.post(
            url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # Логируем сырой ответ
        logger.info(f"Raw API response: {response.status_code}, {response.text}")
        
        # Обрабатываем 500 ошибку особым образом
        if response.status_code == 500:
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    raise Exception(f"API Error: {error_data['detail']}")
            except ValueError:
                raise Exception(f"API returned 500: {response.text}")
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        raise Exception(f"API request failed: {str(e)}")
     
def telegram_auth_required(f):
    """Декоратор для проверки авторизации через Telegram"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if DEBUG_MODE:
            session['authorized'] = True
            session['user_id'] = DEV_USER_ID
            return f(*args, **kwargs)
            
        if not session.get('authorized'):
            logger.warning("Unauthorized access attempt")
            return jsonify({"status": "error", "message": "Authorization required"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

# Базовые роуты
@application.route("/")
def index():
    logger.info("Rendering mining page")
    return render_template("mining.html")

@application.route("/profile")
def profile():
    logger.info("Rendering profile page")
    return render_template("profile.html")

@application.route('/get_init_data')
def get_init_data():
    if DEBUG_MODE:
        user_data = {
            "id": DEV_USER_ID,
            "first_name": "Dev",
            "last_name": "Mode",
            "username": "devuser",
            "language_code": "ru"
        }
        fake_init_data = f"user={json.dumps(user_data)}"
        return jsonify({"status": "success", "init_data": fake_init_data})
    
    try:
        init_data = request.cookies.get('initDataRaw')
        if not init_data:
            return jsonify({"status": "error", "message": "Init data missing"}), 400
        return jsonify({"status": "success", "init_data": init_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@application.route('/auth')
def auth():
    if DEBUG_MODE and 'initData' not in request.args:
        logger.info("DEV MODE: Using test user data")
        session['authorized'] = True
        session['user_id'] = DEV_USER_ID
        return jsonify({"status": "success", "user_id": DEV_USER_ID})

    init_data = request.args.get('initData')
    if not init_data:
        return jsonify({"status": "error", "message": "Missing initData"}), 400

    try:
        parsed = parse_qs(init_data)
        user_json = unquote(parsed.get('user', ['{}'])[0])
        user_data = json.loads(user_json)
        
        session['authorized'] = True
        session['user_id'] = user_data.get('id')
        
        return jsonify({"status": "success", "user_id": session['user_id']})
    except Exception as e:
        logger.error(f'Auth error: {str(e)}')
        return jsonify({"status": "error", "message": "Auth failed"}), 400

# User Endpoints
@application.route("/get_user_data", methods=["GET", "POST"])
def get_user_data():
    try:
        user_id = session.get('user_id', request.args.get('user_id') if request.method == 'GET' else request.json.get('user_id'))
        
        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        # Получаем данные пользователя
        user_response = make_api_request("get_user", {"user_id": user_id})
        balance_response = make_api_request("get_balance", {"user_id": user_id})
        
        return jsonify({
            "status": "success",
            "user": {
                "user_id": user_response.get("user_id"),
                "first_name": user_response.get("first_name"),
                "last_name": user_response.get("last_name"),
                "username": user_response.get("username"),
                "language_code": user_response.get("language_code"),
                "balance": balance_response.get("balance", 0),
                "rub_balance": user_response.get("rub_balance", 0),
                "prem": user_response.get("prem", 0),
                "reg_time": user_response.get("reg_time")
            }
        })
    except Exception as e:
        logger.error(f"Error in get_user_data: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@application.route("/get_user_balance", methods=["GET"])
def get_user_balance():
    try:
        user_id = request.args.get('user_id', DEV_USER_ID if DEBUG_MODE else None)
        
        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        response = make_api_request("get_balance", {"user_id": user_id})
        return jsonify({
            "status": "success",
            "balance": response.get("balance", 0),
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"Error in get_user_balance: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
# Mining Endpoints
@application.route("/mining/start", methods=["POST"])
def start_mining():
    try:
        data = request.json
        response = make_api_request("mining/start", {
            "user_id": data.get('user_id'),
            "deposit": data.get('deposit', 1)
        })
        
        # Обработка успешного ответа
        if response.get("status") == "success":
            return jsonify({
                "status": "success",
                "message": "Майнинг успешно активирован"
            })
        
        # Обработка ошибок от API
        return jsonify({
            "status": "error",
            "message": response.get("detail", "Неизвестная ошибка при активации майнинга")
        }), 400
        
    except Exception as e:
        logger.error(f"Error in start_mining: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Внутренняя ошибка сервера при активации майнинга"
        }), 500

@application.route("/mining/status", methods=["POST"])
def mining_status():
    try:
        user_id = request.json['user_id']
    
        try:
            api_response = make_api_request("mining/status", {"user_id": user_id})
            
            # Проверяем структуру ответа
            if not isinstance(api_response, dict):
                raise ValueError("Invalid API response format")

            # Формируем полный ответ с учетом нового API
            if api_response.get("is_active", False):
                return jsonify({
                    "is_active": True,
                    "message": "Майнинг активен",
                    "earnings": float(api_response.get("earnings", 0.0)),
                    "time_left": api_response.get("time_left", "Максимум"),
                    "mined_time": api_response.get("mined_time", "0м"),
                    "can_collect": api_response.get("can_collect", False),
                    "deposit": api_response.get("deposit", 1)
                })
            else:
                return jsonify({
                    "is_active": False,
                    "message": "Майнинг не активен",
                    "earnings": 0.0,
                    "time_left": None,
                    "mined_time": "0м",
                    "can_collect": False,
                    "deposit": 0
                })
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Mining API connection error: {str(e)}")
            return jsonify({
                "is_active": False,
                "message": "Сервер майнинга временно недоступен",
                "earnings": 0.0,
                "time_left": None,
                "mined_time": "0м",
                "can_collect": False,
                "deposit": 0
            }), 503
            
        except ValueError as e:
            logger.error(f"Mining API response error: {str(e)}")
            return jsonify({
                "is_active": False,
                "message": "Ошибка обработки данных майнинга",
                "earnings": 0.0,
                "time_left": None,
                "mined_time": "0м",
                "can_collect": False,
                "deposit": 0
            }), 502

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({
            "is_active": False,
            "message": "Внутренняя ошибка сервера",
            "earnings": 0.0,
            "time_left": None,
            "mined_time": "0м",
            "can_collect": False,
            "deposit": 0
        }), 500
    
@application.route("/mining/stop", methods=["POST"])
def stop_mining():
    try:
        data = request.json
        response = make_api_request("mining/stop", {
            "user_id": data.get('user_id')
        })
        
        # Обработка успешного ответа
        if response.get("status") == "success":
            return jsonify({
                "status": "success",
                "message": "Майнинг успешно остановлен"
            })
        
        # Обработка ошибок от API
        return jsonify({
            "status": "error",
            "message": response.get("detail", "Неизвестная ошибка при остановке майнинга")
        }), 400
        
    except Exception as e:
        logger.error(f"Error in stop_mining: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Внутренняя ошибка сервера при остановке майнинга"
        }), 500

@application.route("/mining/collect", methods=["POST"])
def collect_mining():
    try:
        data = request.json
        response = make_api_request("mining/collect", {
            "user_id": data.get('user_id')
        })
        
        # Обработка успешного ответа
        if response.get("status") == "success":
            return jsonify({
                "status": "success",
                "amount": response.get("amount", 0),
                "message": f"Успешно собрано {response.get('amount', 0):.2f} монет"
            })
        
        # Обработка ошибок от API
        error_message = response.get("detail", "Неизвестная ошибка при сборе майнинга")
        return jsonify({
            "status": "error",
            "message": error_message
        }), 400
        
    except Exception as e:
        logger.error(f"Error in collect_mining: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Внутренняя ошибка сервера при сборе майнинга"
        }), 500

@application.route("/mining/stats", methods=["GET"])
def mining_stats():
    try:
        response = make_api_request("mining/stats", method='GET')
        
        # Обработка успешного ответа
        if isinstance(response, dict) and response.get("status") == "success":
            return jsonify({
                "status": "success",
                "total_miners": response.get("total_miners", 0)
            })
        
        # Обработка ошибок от API
        return jsonify({
            "status": "error",
            "message": "Не удалось получить статистику майнинга"
        }), 400
        
    except Exception as e:
        logger.error(f"Error in mining_stats: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Внутренняя ошибка сервера при получении статистики"
        }), 500
# Дополнительные функции
@application.route("/me", methods=["GET"])
def me():
    try:
        if DEBUG_MODE:
            return jsonify({
                "status": "success",
                "user": {
                    "user_id": DEV_USER_ID,
                    "first_name": "Dev",
                    "last_name": "User",
                    "username": "devuser",
                    "language_code": "en",
                    "balance": 1000.50
                }
            })
            
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "User not authenticated"}), 401

        user_response = make_api_request("get_user", {"user_id": user_id})
        balance_response = make_api_request("get_balance", {"user_id": user_id})
        
        return jsonify({
            "status": "success",
            "user": {
                "user_id": user_response.get("user_id"),
                "first_name": user_response.get("first_name"),
                "last_name": user_response.get("last_name"),
                "username": user_response.get("username"),
                "language_code": user_response.get("language_code"),
                "balance": balance_response.get("balance", 0)
            }
        })
    except Exception as e:
        logger.error(f"Error in /me: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@application.route("/logout", methods=["POST"])
def logout():
    session.clear()
    logger.info("User logged out")
    return jsonify({"status": "success", "message": "Logged out successfully"})

@application.route('/get_config')
def get_config():
    return jsonify({
        'DEBUG_MODE': DEBUG_MODE,
        'DEV_USER_ID': DEV_USER_ID
    })

if __name__ == "__main__":
    try:
        logger.info(f"Starting application in {'DEV' if DEBUG_MODE else 'PROD'} mode")
        application.run(host='0.0.0.0', port=5000, debug=DEBUG_MODE)
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")