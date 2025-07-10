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
const bot_1 = require("../bot");
const wallets_1 = require("../ton-connect/wallets");
const connector_1 = require("../ton-connect/connector");
const qrcode_1 = __importDefault(require("qrcode"));
function handleConnectCommand(msg) {
    return __awaiter(this, void 0, void 0, function* () {
        const chatId = msg.chat.id;
        const wallets = yield (0, wallets_1.getWallets)();
        const connector = (0, connector_1.getConnector)(chatId);
        connector.onStatusChange((wallet) => __awaiter(this, void 0, void 0, function* () {
            if (wallet) {
                const walletInfo = yield (0, wallets_1.getWalletInfo)(wallet.device.appName);
                const walletName = (walletInfo === null || walletInfo === void 0 ? void 0 : walletInfo.name) || wallet.device.appName;
                console.log(`Wallet connected: ${walletName}`, wallet.device);
                try {
                    yield bot_1.bot.sendMessage(chatId, `✅ Кошелек ${walletName} успешно подключен!\n\n` +
                        `Версия: ${wallet.device.appVersion}\n` +
                        `Платформа: ${wallet.device.platform}`);
                }
                catch (err) {
                    console.error('Failed to send message:', err);
                }
            }
        }));
        const link = connector.connect(wallets);
        const image = yield qrcode_1.default.toBuffer(link);
        yield bot_1.bot.sendPhoto(chatId, image, {
            reply_markup: {
                inline_keyboard: [
                    [
                        { text: 'Выбрать кошелек', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
                        { text: 'Открыть ссылку', url: `https://ton-connect.github.io/open-tc?connect=${encodeURIComponent(link)}` }
                    ]
                ]
            }
        });
    });
}
exports.handleConnectCommand = handleConnectCommand;
// Адрес получателя (замени на свой TON-адрес)
const RECEIVER_WALLET_ADDRESS = 'UQBKc7lifQe_U4cUibpyY5J5AQF7hRIPXIJZvuohf0x4E1n1'; // ← замени обязательно
bot_1.bot.onText(/\/pay (\d+(?:\.\d+)?)/, (msg, match) => __awaiter(void 0, void 0, void 0, function* () {
    const chatId = msg.chat.id;
    const amountTON = parseFloat((match === null || match === void 0 ? void 0 : match[1]) || '0');
    if (!amountTON || isNaN(amountTON) || amountTON <= 0) {
        yield bot_1.bot.sendMessage(chatId, 'Введите сумму в тонах, например: /pay 1.5');
        return;
    }
    const connector = (0, connector_1.getConnector)(chatId);
    // ✅ Проверка подключения
    const connectedWallet = connector.wallet;
    if (!connectedWallet) {
        yield bot_1.bot.sendMessage(chatId, 'Сначала подключите кошелёк с помощью команды /connect');
        return;
    }
    const amountNanoTON = Math.floor(amountTON * 1e9).toString();
    const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 600,
        messages: [
            {
                address: RECEIVER_WALLET_ADDRESS,
                amount: amountNanoTON
                // payload и stateInit можно не указывать
            }
        ]
    };
    try {
        yield connector.sendTransaction(transaction);
        yield bot_1.bot.sendMessage(chatId, `Запрос на оплату ${amountTON} TON отправлен. Подтвердите в кошельке.`);
    }
    catch (err) {
        console.error('Ошибка при отправке платежа', err);
        yield bot_1.bot.sendMessage(chatId, 'Ошибка при отправке платежа. Убедитесь, что кошелёк подключён.');
    }
}));
//# sourceMappingURL=handleConnectCommand.js.map