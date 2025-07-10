"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const bot_1 = require("./bot");
const handleConnectCommand_1 = require("./commands/handleConnectCommand");
require("./ton-connect/connect-wallet-menu"); // важно, чтобы путь был корректный!
bot_1.bot.onText(/\/connect/, handleConnectCommand_1.handleConnectCommand);
//# sourceMappingURL=main.js.map