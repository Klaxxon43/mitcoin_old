"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
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
exports.walletMenuCallbacks = void 0;
const wallets_1 = require("./wallets");
const bot_1 = require("../bot");
const connector_1 = require("./connector");
const qrcode_1 = __importDefault(require("qrcode"));
const fs = __importStar(require("fs"));
exports.walletMenuCallbacks = {
    choose_wallet: onChooseWalletClick,
    select_wallet: onWalletClick,
    universal_qr: onOpenUniversalQRClick
};
bot_1.bot.on('callback_query', (query) => __awaiter(void 0, void 0, void 0, function* () {
    if (!query.data)
        return;
    let req;
    try {
        req = JSON.parse(query.data);
    }
    catch (_a) {
        return;
    }
    const handler = exports.walletMenuCallbacks[req.method];
    if (handler)
        yield handler(query, req.data);
}));
function onChooseWalletClick(query) {
    return __awaiter(this, void 0, void 0, function* () {
        const wallets = yield (0, wallets_1.getWallets)();
        // Группируем кошельки по 2 в ряд
        const walletButtons = [];
        for (let i = 0; i < wallets.length; i += 2) {
            const row = wallets.slice(i, i + 2).map(w => ({
                text: w.name,
                callback_data: JSON.stringify({ method: 'select_wallet', data: w.appName })
            }));
            walletButtons.push(row);
        }
        // Добавляем кнопку "Назад"
        walletButtons.push([
            { text: '« Back', callback_data: JSON.stringify({ method: 'universal_qr' }) }
        ]);
        yield bot_1.bot.editMessageReplyMarkup({
            inline_keyboard: walletButtons
        }, {
            chat_id: query.message.chat.id,
            message_id: query.message.message_id
        });
    });
}
function onOpenUniversalQRClick(query) {
    return __awaiter(this, void 0, void 0, function* () {
        const chatId = query.message.chat.id;
        const wallets = yield (0, wallets_1.getWallets)();
        const connector = (0, connector_1.getConnector)(chatId);
        const link = connector.connect(wallets);
        yield editQR(query.message, link);
        yield bot_1.bot.editMessageReplyMarkup({
            inline_keyboard: [
                [
                    { text: 'Choose a Wallet', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
                    { text: 'Open Link', url: `https://ton-connect.github.io/open-tc?connect=${encodeURIComponent(link)}` }
                ]
            ]
        }, {
            chat_id: chatId,
            message_id: query.message.message_id
        });
    });
}
function onWalletClick(query, appName) {
    return __awaiter(this, void 0, void 0, function* () {
        const chatId = query.message.chat.id;
        const connector = (0, connector_1.getConnector)(chatId);
        const wallet = yield (0, wallets_1.getWalletInfo)(appName);
        if (!wallet)
            return;
        connector.onStatusChange((connectedWallet) => __awaiter(this, void 0, void 0, function* () {
            if (connectedWallet) {
                const walletName = wallet.name || connectedWallet.device.appName;
                yield bot_1.bot.sendMessage(chatId, `✅ Кошелек ${walletName} успешно подключен!\n\n` +
                    `Версия: ${connectedWallet.device.appVersion}\n` +
                    `Платформа: ${connectedWallet.device.platform}`);
            }
        }));
        const link = connector.connect({
            bridgeUrl: wallet.bridgeUrl,
            universalLink: wallet.universalLink
        });
        yield editQR(query.message, link);
        yield bot_1.bot.editMessageReplyMarkup({
            inline_keyboard: [
                [
                    { text: '« Назад', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
                    { text: `Открыть ${wallet.name}`, url: link }
                ]
            ]
        }, {
            chat_id: chatId,
            message_id: query.message.message_id
        });
    });
}
function editQR(msg, link) {
    return __awaiter(this, void 0, void 0, function* () {
        const file = `qr-${Date.now()}.png`;
        yield qrcode_1.default.toFile(file, link);
        yield bot_1.bot.editMessageMedia({ type: 'photo', media: `attach://${file}` }, {
            chat_id: msg.chat.id,
            message_id: msg.message_id
        });
        yield fs.promises.unlink(file);
    });
}
//# sourceMappingURL=connect-wallet-menu.js.map