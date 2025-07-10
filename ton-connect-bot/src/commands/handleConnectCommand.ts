import { bot } from '../bot';
import { getWallets, getWalletInfo } from '../ton-connect/wallets';
import { getConnector } from '../ton-connect/connector';
import QRCode from 'qrcode';
import type TelegramBot from 'node-telegram-bot-api';

export async function handleConnectCommand(msg: TelegramBot.Message) {
    const chatId = msg.chat.id;
    const wallets = await getWallets();
    const connector = getConnector(chatId);
  
    connector.onStatusChange(async (wallet) => {
      if (wallet) {
        const walletInfo = await getWalletInfo(wallet.device.appName);
        const walletName = walletInfo?.name || wallet.device.appName;
        
        console.log(`Wallet connected: ${walletName}`, wallet.device);
        
        try {
          await bot.sendMessage(
            chatId, 
            `✅ Кошелек ${walletName} успешно подключен!\n\n` +
            `Версия: ${wallet.device.appVersion}\n` +
            `Платформа: ${wallet.device.platform}`
          );
        } catch (err) {
          console.error('Failed to send message:', err);
        }
      }
    });
  
    const link = connector.connect(wallets);
    const image = await QRCode.toBuffer(link);
  
    await bot.sendPhoto(chatId, image, {
      reply_markup: {
        inline_keyboard: [
          [
            { text: 'Выбрать кошелек', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
            { text: 'Открыть ссылку', url: `https://ton-connect.github.io/open-tc?connect=${encodeURIComponent(link)}` }
          ]
        ]
      }
    });
  }


// Адрес получателя (замени на свой TON-адрес)
const RECEIVER_WALLET_ADDRESS = 'UQBKc7lifQe_U4cUibpyY5J5AQF7hRIPXIJZvuohf0x4E1n1'; // ← замени обязательно

bot.onText(/\/pay (\d+(?:\.\d+)?)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const amountTON = parseFloat(match?.[1] || '0');

  if (!amountTON || isNaN(amountTON) || amountTON <= 0) {
    await bot.sendMessage(chatId, 'Введите сумму в тонах, например: /pay 1.5');
    return;
  }

  const connector = getConnector(chatId);

  // ✅ Проверка подключения
  const connectedWallet = connector.wallet;
  if (!connectedWallet) {
    await bot.sendMessage(chatId, 'Сначала подключите кошелёк с помощью команды /connect');
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
    await connector.sendTransaction(transaction);
    await bot.sendMessage(chatId, `Запрос на оплату ${amountTON} TON отправлен. Подтвердите в кошельке.`);
  } catch (err) {
    console.error('Ошибка при отправке платежа', err);
    await bot.sendMessage(chatId, 'Ошибка при отправке платежа. Убедитесь, что кошелёк подключён.');
  }
});