import requests, json
import db

MAINNET_API_BASE = "https://toncenter.com/api/v2/"
TESTNET_API_BASE = "https://testnet.toncenter.com/api/v2/"

config = json.load(open('config.json'))
API_BASE = MAINNET_API_BASE if config["WORK_MODE"]=="mainnet" else TESTNET_API_BASE
API_TOKEN = config["MAINNET_API_TOKEN"] if config["WORK_MODE"]=="mainnet" else config["TESTNET_API_TOKEN"]
WALLET = config["MAINNET_WALLET"] if config["WORK_MODE"]=="mainnet" else config["TESTNET_WALLET"]


def detect_address(address: str) -> str | bool:
    try:
        resp = requests.get(
            f"{API_BASE}accounts/{address}",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            timeout=10
        )
        data = resp.json()
        print(f"[DEBUG] detectAddress: {data}")
        return data["address"]["bounceable"]
    except Exception as e:
        print(f"[detect_address] Ошибка: {e}")
        return False

def get_address_transactions():
    url = f"{API_BASE}getTransactions?address={WALLET}&limit=30&archival=true&api_key={API_TOKEN}"
    return requests.get(url).json().get('result', [])

def find_transaction(user_wallet, value, comment):
    for tx in get_address_transactions():
        msg = tx['in_msg']
        if msg['source']==user_wallet and msg['value']==value and msg['message']==comment:
            if not db.check_transaction(msg['body_hash']):
                db.add_v_transaction(msg['source'], msg['body_hash'], msg['value'], msg['message'])
                return True
    return False
