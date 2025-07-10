# api.py
import requests
import json
import time
import db

MAINNET_API_BASE = "https://toncenter.com/api/v2/"
TESTNET_API_BASE = "https://testnet.toncenter.com/api/v2/"

with open('config.json', 'r') as f:
    config_json = json.load(f)
    MAINNET_API_TOKEN = config_json['MAINNET_API_TOKEN']
    TESTNET_API_TOKEN = config_json['TESTNET_API_TOKEN']
    MAINNET_WALLET = config_json['MAINNET_WALLET']
    TESTNET_WALLET = config_json['TESTNET_WALLET']
    WORK_MODE = config_json['WORK_MODE']

if WORK_MODE == "mainnet":
    API_BASE = MAINNET_API_BASE
    API_TOKEN = MAINNET_API_TOKEN
    WALLET = MAINNET_WALLET
else:
    API_BASE = TESTNET_API_BASE
    API_TOKEN = TESTNET_API_TOKEN
    WALLET = TESTNET_WALLET

def find_transaction(value: str, comment: str) -> bool:
    try:
        print(f"\n[Debug] Ищем платеж: amount={value}, comment='{comment}'")
        
        response = requests.get(
            f"{API_BASE}getTransactions",
            params={
                'address': WALLET,
                'limit': 100,
                'api_key': API_TOKEN,
                'archival': True
            },
            timeout=10
        )
        
        print(f"[Debug] Статус: {response.status_code}")
        
        data = response.json()
        if not data.get('ok', False):
            print(f"[Error] TonCenter error: {data.get('error')}")
            return False

        for tx in data.get('result', []):
            in_msg = tx.get('in_msg', {})
            print(f"\n[Debug] Проверяем tx: hash={tx.get('hash')}")
            print(f"Сумма: {in_msg.get('value')} (нужно: {value})")
            print(f"Комментарий: '{in_msg.get('message')}' (нужно: '{comment}')")
            
            # Сравниваем сумму и комментарий
            if (str(in_msg.get('value')) == value and 
                in_msg.get('message', '').strip() == comment.strip()):
                print("[Success] Транзакция найдена!")
                return True

        print("[Debug] Подходящая транзакция не найдена.")
        return False

    except Exception as e:
        print(f"[Critical Error] {type(e)}: {str(e)}")
        return False