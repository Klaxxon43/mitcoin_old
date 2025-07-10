import json
import logging
import requests

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
import db  # твой модуль с функциями работы с SQLite

logging.basicConfig(level=logging.INFO)

config = json.load(open('config.json'))

BOT_TOKEN = config['BOT_TOKEN']
MAINNET_WALLET = config['MAINNET_WALLET']
TESTNET_WALLET = config['TESTNET_WALLET']
WORK_MODE = config['WORK_MODE']

MAINNET_API_BASE = "https://toncenter.com/api/v2/"
TESTNET_API_BASE = "https://testnet.toncenter.com/api/v2/"

API_BASE = MAINNET_API_BASE if WORK_MODE == "mainnet" else TESTNET_API_BASE
API_TOKEN = config["MAINNET_API_TOKEN"] if WORK_MODE == "mainnet" else config["TESTNET_API_TOKEN"]
WALLET = MAINNET_WALLET if WORK_MODE == "mainnet" else TESTNET_WALLET

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class DataInput(StatesGroup):
    WalletState = State()
    PayState = State()


def detect_address(address: str):
    url = f"{API_BASE}detectAddress?address={address}&api_key={API_TOKEN}"
    r = requests.get(url).json()
    return r.get('result', {}).get('bounceable', {}).get('b64url') or False


def get_address_transactions():
    url = f"{API_BASE}getTransactions?address={WALLET}&limit=30&archival=true&api_key={API_TOKEN}"
    return requests.get(url).json().get('result', [])


def find_transaction(user_wallet, value, comment):
    for tx in get_address_transactions():
        msg = tx['in_msg']
        if msg['source'] == user_wallet and msg['value'] == value and msg['message'] == comment:
            if not db.check_transaction(msg['body_hash']):
                db.add_v_transaction(msg['source'], msg['body_hash'], msg['value'], msg['message'])
                return True
    return False


@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message, state: FSMContext):
    user_exists = db.check_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(f"Привет, {message.from_user.first_name}! Отправь свой TON кошелек для привязки.")
    await state.set_state(DataInput.WalletState)


@dp.message(DataInput.WalletState)
async def wallet_input(message: Message, state: FSMContext):
    address = message.text.strip()
    bounceable = detect_address(address)
    if not bounceable:
        await message.answer("Пожалуйста, отправьте корректный адрес TON кошелька.")
        return

    updated = db.v_wallet(message.from_user.id, bounceable)
    if updated is True:
        await message.answer(f"Ваш кошелек {bounceable} привязан успешно!")
    else:
        await message.answer(f"Ваш кошелек уже привязан: {updated}")

    await state.clear()


@dp.message(Command(commands=["check_payments"]))
async def check_payments(message: Message):
    payments = db.get_user_payments(message.from_user.id)
    if isinstance(payments, str):
        await message.answer(payments)
    elif payments:
        text = "Ваши платежи:\n"
        for p in payments:
            text += f"Сумма: {p['value']} nanotons, Комментарий: {p['comment']}\n"
        await message.answer(text)
    else:
        await message.answer("Платежей не найдено.")


@dp.message(Command(commands=["pay"]))
async def pay_start(message: Message, state: FSMContext):
    await message.answer("Отправьте сумму платежа (в nanotons):")
    await state.set_state(DataInput.PayState)


@dp.message(DataInput.PayState)
async def pay_value(message: Message, state: FSMContext):
    try:
        value = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число, пожалуйста.")
        return

    wallet = db.get_user_wallet(message.from_user.id)
    if wallet == "none":
        await message.answer("Сначала привяжите кошелек с помощью /start")
        await state.clear()
        return

    comment = f"payment_from_{message.from_user.id}"
    await message.answer(
        f"Отправьте на кошелек {WALLET} сумму {value} nanotons с комментарием: {comment}\n"
        "После оплаты используйте команду /confirm для проверки."
    )
    await state.update_data(value=value, comment=comment)
    await state.clear()


@dp.message(Command(commands=["confirm"]))
async def confirm_payment(message: Message, state: FSMContext):
    user_data = await state.get_data()
    value = user_data.get('value')
    comment = user_data.get('comment')
    wallet = db.get_user_wallet(message.from_user.id)

    if not value or not comment or wallet == "none":
        await message.answer("Нет данных для проверки. Сначала создайте платеж через /pay")
        return

    found = find_transaction(wallet, value, comment)
    if found:
        await message.answer("Платеж подтверждён и добавлен в базу.")
    else:
        await message.answer("Платеж не найден. Проверьте сумму, комментарий и повторите позже.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(dp.start_polling(bot))
