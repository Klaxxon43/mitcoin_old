from handlers.client import *
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

MINI_APP_URL = "https://mitcoin.ru"
WELCOME_IMAGE_PATH = 'prview.png'

WELCOME_MESSAGE = (
    "👋 Welcome to my Demo Bot!\n\n"
    "This bot demonstrates basic Telegram bot functionality "
    "and integration with Telegram Mini Apps.\n\n"
    "🔍 Features:\n"
    "- Basic command handling\n"
    "- Inline keyboard integration\n"
    "- Mini App integration\n\n"
    "Click the button below to open my Mini App!"
)

@router.message(Command('app'))
async def app_open(message: types.Message):

    logger.info(f"User {message.from_user.id} started the bot")
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Open Mini App",
        web_app=WebAppInfo(url=MINI_APP_URL)
    ))
    
    try:
        with open(WELCOME_IMAGE_PATH, 'rb') as photo:
            await message.answer_photo(
                photo=photo,
                caption=WELCOME_MESSAGE,
                reply_markup=builder.as_markup()
            )
    except FileNotFoundError:
        logger.error(f"Welcome image not found at {WELCOME_IMAGE_PATH}")
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=builder.as_markup()
        )