import requests
import json

# Конфигурация
BASE_URL = "http://45.143.203.232:8000"
TEST_USER_ID = 5129878568

def print_response(response):
    """Печатает информацию о response"""
    print(f"URL: {response.url}")
    print(f"Status code: {response.status_code}")
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except:
        print("Response:", response.text)

def test_ping():
    """Тестирование эндпоинта /ping"""
    print("\n[1] Testing /ping (GET):")
    response = requests.get(f"{BASE_URL}/ping")
    print_response(response)

def test_get_balance():
    """Тестирование /get_balance (POST)"""
    print("\n[2] Testing /get_balance (POST):")
    url = f"{BASE_URL}/get_balance"
    data = {"user_id": TEST_USER_ID}
    
    response = requests.post(url, json=data)
    print_response(response)

def test_get_user():
    """Тестирование /get_user (POST)"""
    print("\n[3] Testing /get_user (POST):")
    url = f"{BASE_URL}/get_user"
    data = {"user_id": TEST_USER_ID}
    
    response = requests.post(url, json=data)
    print_response(response)

def test_mining_flow():
    """Тестирование полного цикла майнинга"""
    print("\n[4] Testing mining flow:")
    
    # 1. Старт майнинга
    print("\n[4.1] Starting mining:")
    response = requests.post(
        f"{BASE_URL}/mining/start",
        json={"user_id": TEST_USER_ID, "deposit": 1}
    )
    print_response(response)
    
    # 2. Проверка статуса
    print("\n[4.2] Checking status:")
    response = requests.post(
        f"{BASE_URL}/mining/status",
        json={"user_id": TEST_USER_ID}
    )
    print_response(response)
    
    # 3. Остановка майнинга
    print("\n[4.3] Stopping mining:")
    response = requests.post(
        f"{BASE_URL}/mining/stop",
        json={"user_id": TEST_USER_ID}
    )
    print_response(response)

def test_mining_stats():
    """Тестирование /mining/stats (GET)"""
    print("\n[5] Testing /mining/stats (GET):")
    response = requests.get(f"{BASE_URL}/mining/stats")
    print_response(response)

if __name__ == "__main__":
    print(f"Testing API at {BASE_URL}")
    
    test_ping()          # GET /ping
    test_get_balance()   # POST /get_balance
    test_get_user()      # POST /get_user
    test_mining_flow()   # Полный цикл майнинга
    test_mining_stats()  # GET /mining/stats