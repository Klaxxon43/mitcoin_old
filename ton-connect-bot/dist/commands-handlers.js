"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleConnectCommand = void 0;
const bot_1 = require("./bot");
const wallets_1 = require("./ton-connect/wallets");
const connector_1 = require("./ton-connect/connector");
const qrcode_1 = __importDefault(require("qrcode"));
function handleConnectCommand(msg) {
    return __awaiter(this, void 0, void 0, function* () {
        const chatId = msg.chat.id;
        const wallets = yield (0, wallets_1.getWallets)();
        const connector = (0, connector_1.getConnector)(chatId);
        connector.onStatusChange(wallet => {
            if (wallet)
                bot_1.bot.sendMessage(chatId, `${wallet.device.appName} wallet connected!`);
        });
        const link = connector.connect(wallets);
        const image = yield qrcode_1.default.toBuffer(link);
        yield bot_1.bot.sendPhoto(chatId, image, {
            reply_markup: {
                inline_keyboard: [
                    [
                        { text: 'Choose a Wallet', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
                        { text: 'Open Link', url: `https://ton-connect.github.io/open-tc?connect=${encodeURIComponent(link)}` }
                    ]
                ]
            }
        });
    });
}
exports.handleConnectCommand = handleConnectCommand;
//# sourceMappingURL=commands-handlers.js.map