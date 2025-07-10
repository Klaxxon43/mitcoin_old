import requests

API_KEY = "f8e79e787c66fbb7a10ef3e2456151e9e3c3f5b74e6231b85ba08be5a9d5359b"
response = requests.get(
    "https://toncenter.com/api/v2/getWalletInformation",
    params={
        "address": "UQBKc7lifQe_U4cUibpyY5J5AQF7hRIPXIJZvuohf0x4E1n1",  # любой рабочий mainnet-адрес
        "api_key": API_KEY
    }
)
print(response.status_code, response.json())