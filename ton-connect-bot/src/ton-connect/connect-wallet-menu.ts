import TelegramBot, { CallbackQuery } from 'node-telegram-bot-api';
import { getWallets, getWalletInfo } from './wallets';
import { bot } from '../bot';
import { getConnector } from './connector';
import QRCode from 'qrcode';
import * as fs from 'fs';

export const walletMenuCallbacks = {
  choose_wallet: onChooseWalletClick,
  select_wallet: onWalletClick,
  universal_qr: onOpenUniversalQRClick
};

bot.on('callback_query', async query => {
  if (!query.data) return;
  let req;
  try {
    req = JSON.parse(query.data);
  } catch {
    return;
  }
  const handler = walletMenuCallbacks[req.method as keyof typeof walletMenuCallbacks];
  if (handler) await handler(query, req.data);
});

async function onChooseWalletClick(query: CallbackQuery) {
  const wallets = await getWallets();
  
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

  await bot.editMessageReplyMarkup({
    inline_keyboard: walletButtons
  }, {
    chat_id: query.message!.chat.id,
    message_id: query.message!.message_id
  });
}

async function onOpenUniversalQRClick(query: CallbackQuery) {
  const chatId = query.message!.chat.id;
  const wallets = await getWallets();
  const connector = getConnector(chatId);
  const link = connector.connect(wallets);
  await editQR(query.message!, link);
  await bot.editMessageReplyMarkup({
    inline_keyboard: [
      [
        { text: 'Choose a Wallet', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
        { text: 'Open Link', url: `https://ton-connect.github.io/open-tc?connect=${encodeURIComponent(link)}` }
      ]
    ]
  }, {
    chat_id: chatId,
    message_id: query.message!.message_id
  });
}

async function onWalletClick(query: CallbackQuery, appName: string) {
  const chatId = query.message!.chat.id;
  const connector = getConnector(chatId);
  const wallet = await getWalletInfo(appName);
  if (!wallet) return;

  connector.onStatusChange(async (connectedWallet) => {
    if (connectedWallet) {
      const walletName = wallet.name || connectedWallet.device.appName;
      await bot.sendMessage(
        chatId,
        `✅ Кошелек ${walletName} успешно подключен!\n\n` +
        `Версия: ${connectedWallet.device.appVersion}\n` +
        `Платформа: ${connectedWallet.device.platform}`
      );
    }
  });

  const link = connector.connect({
    bridgeUrl: wallet.bridgeUrl,
    universalLink: wallet.universalLink
  });

  await editQR(query.message!, link);

  await bot.editMessageReplyMarkup({
    inline_keyboard: [
      [
        { text: '« Назад', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
        { text: `Открыть ${wallet.name}`, url: link }
      ]
    ]
  }, {
    chat_id: chatId,
    message_id: query.message!.message_id
  });
}


async function editQR(msg: TelegramBot.Message, link: string) {
  const file = `qr-${Date.now()}.png`;
  await QRCode.toFile(file, link);
  await bot.editMessageMedia({ type: 'photo', media: `attach://${file}` }, {
    chat_id: msg.chat.id,
    message_id: msg.message_id
  });
  await fs.promises.unlink(file);
}

