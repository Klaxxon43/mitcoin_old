import TelegramBot from 'node-telegram-bot-api';
import process from 'process';

const token = process.env.TELEGRAM_BOT_TOKEN!;
if (!token) {
  throw new Error('TELEGRAM_BOT_TOKEN is not set in .env');
}

export const bot = new TelegramBot(token, { polling: true });
