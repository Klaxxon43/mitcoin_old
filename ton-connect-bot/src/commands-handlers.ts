import { bot } from './bot';
import { getWallets } from './ton-connect/wallets';
import { getConnector } from './ton-connect/connector';
import QRCode from 'qrcode';
import type TelegramBot from 'node-telegram-bot-api';

export async function handleConnectCommand(msg: TelegramBot.Message) {
  const chatId = msg.chat.id;
  const wallets = await getWallets();
  const connector = getConnector(chatId);
  connector.onStatusChange(wallet => {
    if (wallet) bot.sendMessage(chatId, `${wallet.device.appName} wallet connected!`);
  });
  const link = connector.connect(wallets);
  const image = await QRCode.toBuffer(link);
  await bot.sendPhoto(chatId, image, {
    reply_markup: {
      inline_keyboard: [
        [
          { text: 'Choose a Wallet', callback_data: JSON.stringify({ method: 'choose_wallet' }) },
          { text: 'Open Link', url: `https://ton-connect.github.io/open-tc?connect=${encodeURIComponent(link)}` }
        ]
      ]
    }
  });
}
