import dotenv from 'dotenv';
dotenv.config();

import { bot } from './bot';
import { handleConnectCommand } from './commands/handleConnectCommand';
import './ton-connect/connect-wallet-menu'; // важно, чтобы путь был корректный!

bot.onText(/\/connect/, handleConnectCommand);
