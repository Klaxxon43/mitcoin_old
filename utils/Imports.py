# Стандартные библиотеки
import os, asyncio, logging, random, uuid, sys, traceback, time, emoji, re, pytz, requests, json, copy
from datetime import datetime
from pathlib import Path
from aiocryptopay import AioCryptoPay, Networks
from cachetools import TTLCache
from typing import Union, Dict, List, Any, Optional


# Aiogram основные компоненты
from aiogram import Bot, F, types, Router, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
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
from config import CRYPTOBOT_TOKEN, ADMINS_ID
from threading import Lock
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECK_CHAT_ID = -1002872158526 # ID чата для проверки заданий
DB_CHAT_ID = -4683486408
INFO_ID = -4784146602
TASKS_CHAT_ID = -1002291978719
REPORT_CHAT_ID = -1002291978719
WITHDRAW_CHAT = -1002684215736#-4705317806


MOSCOW_TZ = pytz.timezone("Europe/Moscow")