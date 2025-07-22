import os
# Задаем переменные окружения
API_TOKEN = '7562196234:AAHdxNWOF8PP-sPL2r0D50RLuQspXedFf7U'
CRYPTOBOT_TOKEN = '275327:AAp2d4Vpr0zMpDYOiyT1MP70KfUpNhSTVys' #312748:AAgftMZCgkWN8rDJ1uL8K1Dcbvd49J51ZeM' 
HOST='0.0.0.0'
PORT=8000
BASE_URL='efnejrnerj' #можно через ngrok
WEBHOOK_PATH = f'/{API_TOKEN}'

TON_API_BASE = "https://toncenter.com/api/v2/"
TON_API_TOKEN = "f8e79e787c66fbb7a10ef3e2456151e9e3c3f5b74e6231b85ba08be5a9d5359b"  # Замени на реальный API ключ от TON Center
TON_WALLET = "UQAKAfkG7XDmKfAwVyziPryAPaArEOS1TWRs4YDagUlwylHg"  # Адрес кошелька для приема платежей

from API.Stream_Promotion_API import StreamPromotionAPI
BotsAPI = StreamPromotionAPI("Cxqup7n2Ca3dh1bbhBM4WoK89k7XMJ83")

APAY_CLIENT_ID = 1080
APAY_SECRET_KEY = "aa75c8bc-19c2-4901-9290-0f1feead864e"

# import os
# # Задаем переменные окружения
# API_TOKEN = '7866394890:AAFSpTKFzbRO9-ZmLFRyI418wUlcCSSijWM'
# CRYPTOBOT_TOKEN = '275327:AAp2d4Vpr0zMpDYOiyT1MP70KfUpNhSTVys'
# HOST='0.0.0.0'
# PORT=8000
# BASE_URL='efnejrnerj' #можно через ngrok
# WEBHOOK_PATH = f'/{API_TOKEN}'
# TON_API_BASE = "https://toncenter.com/api/v2/"
# TON_API_TOKEN = "f8e79e787c66fbb7a10ef3e2456151e9e3c3f5b74e6231b85ba08be5a9d5359b"  # Замени на реальный API ключ от TO>TON_WALLET = "UQAKAfkG7XDmKfAwVyziPryAPaArEOS1TWRs4YDagUlwylHg"  # Адрес кошелька для приема платежей
# from API.Stream_Promotion_API import StreamPromotionAPI
# BotsAPI = StreamPromotionAPI("Cxqup7n2Ca3dh1bbhBM4WoK89k7XMJ83")


# import os
# # Задаем переменные окружения
# API_TOKEN = '7866394890:AAFSpTKFzbRO9-ZmLFRyI418wUlcCSSijWM'
# CRYPTOBOT_TOKEN = '275327:AAp2d4Vpr0zMpDYOiyT1MP70KfUpNhSTVys'
# HOST='0.0.0.0'
# PORT=8000
# BASE_URL='efnejrnerj' #можно через ngrok
# WEBHOOK_PATH = f'/{API_TOKEN}'
# TON_API_BASE = "https://toncenter.com/api/v2/"
# TON_API_TOKEN = "f8e79e787c66fbb7a10ef3e2456151e9e3c3f5b74e6231b85ba08be5a9d5359b"  # Замени на реальный API ключ от TO>TON_WALLET = "UQAKAfkG7XDmKfAwVyziPryAPaArEOS1TWRs4YDagUlwylHg"  # Адрес кошелька для приема платежей
# from API.Stream_Promotion_API import StreamPromotionAPI
# BotsAPI = StreamPromotionAPI("Cxqup7n2Ca3dh1bbhBM4WoK89k7XMJ83")

#telethon
#1
# api_id = '25159668'
# api_hash = '3c0bf4ca735fec3f3cb59302239a0cca'
# phone_number = '+79097217693'

#2
# api_id = '26226969'
# api_hash = 'ad23f103ca534197dca27c8b3b5c98a1'
# phone_number = '+79914512687'

#3
# api_id = '27766851'
# api_hash = '9caf54b36748a7043312fdb202a92ae4'
# phone_number = '+79223348628'

#4
# api_id = '27696906'
# api_hash = '0d03be5be100e1fb520c7acb38ffe74c'
# phone_number = '+79195241549'

#5
# api_id = '26936986'
# api_hash = 'e8ae7ea2e648aeeb1b176342b92fd847'
# phone_number = '+79585478798'

#6
# api_id = '27780099'
# api_hash = '48139036c9adc3df861b5c3a041336da'
# phone_number = '+79951031549'

#7
# api_id = '27599195'
# api_hash = '0dae56e1f2f24c04af88fe36f51d3908'
# phone_number = '+79935976109'


# sessions = [
#     {"session_name": "session_name", "api_id": 25159668, "api_hash": "3c0bf4ca735fec3f3cb59302239a0cca", "phone_number": "+79097217693"},
#     {"session_name": "session_name2", "api_id": 26226969, "api_hash": "ad23f103ca534197dca27c8b3b5c98a1", "phone_number": "+79914512687"},
#     {"session_name": "session_name3", "api_id": 27766851, "api_hash": "9caf54b36748a7043312fdb202a92ae4", "phone_number": "+79223348628"},
#     # {"session_name": "session_name4", "api_id": 27696906, "api_hash": "0d03be5be100e1fb520c7acb38ffe74c", "phone_number": "+79195241549"},
#     # {"session_name": "session_name5", "api_id": 26936986, "api_hash": "e8ae7ea2e648aeeb1b176342b92fd847", "phone_number": "+79585478798"},
#     # {"session_name": "session_name6", "api_id": 27780099, "api_hash": "48139036c9adc3df861b5c3a041336da", "phone_number": "+79951031549"},
#     # {"session_name": "session_name7", "api_id": 27599195, "api_hash": "0dae56e1f2f24c04af88fe36f51d3908", "phone_number": "+79935976109"},
# ]

ADMINS_ID = [996459546, 2118524898, 5492008614, 5129878568]
