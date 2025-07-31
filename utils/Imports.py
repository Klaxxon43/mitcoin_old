# Стандартные библиотеки
import os, asyncio, logging, random, uuid, sys, traceback, time, emoji, re, pytz, requests, json, copy, string, aiohttp, hashlib, colorlog
from datetime import datetime
from pathlib import Path
from aiocryptopay import AioCryptoPay, Networks
from cachetools import TTLCache
from typing import Union, Dict, List, Any, Optional
from aiohttp import ClientError

# Aiogram основные компоненты
from aiogram import Bot, F, types, Router, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import ChatBoostUpdated, ChatBoostRemoved, ChatBoostSourcePremium
from aiogram.enums import ChatBoostSourceType

# Aiogram типы
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, InputMediaPhoto, ChatMemberUpdated,
    ContentType, LabeledPrice, PreCheckoutQuery,
    BufferedInputFile, Chat
)

# Локальные модули
from datebase.db import DB, Promo, Contest, Boost
from utils.kb import *
from confIg import CRYPTOBOT_TOKEN, ADMINS_ID, BotsAPI, TON_WALLET, TON_API_TOKEN, TON_API_BASE, API_TOKEN
from threading import Lock
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

# Получаем корневой логгер
logger = colorlog.getLogger()

# Удаляем все существующие обработчики
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Создаем и добавляем новый обработчик
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    fmt='%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))

logger.addHandler(handler)
logger.setLevel(logging.INFO)

CHECK_CHAT_ID = -1002872158526 # ID чата для проверки заданий
DB_CHAT_ID = -4683486408
INFO_ID = -4812197033
TASKS_CHAT_ID = -1002291978719
REPORT_CHAT_ID = -1002291978719
WITHDRAW_CHAT = -1002684215736#-4705317806
OFFICIAL_CHANNEL_ID = -1002411973361

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

all_price = {
    "channel": 1500,
    "chat": 1500,
    "post": 250,
    "comment": 750,
    "reaction": 500,
    "link": 1500,
    "boost": 5000
}