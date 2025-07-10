// connector.ts
import TonConnect from '@tonconnect/sdk';
import { TonConnectStorage } from './storage';
import * as process from 'process';

const connectors = new Map<number, TonConnect>();

export function getConnector(chatId: number): TonConnect {
  if (connectors.has(chatId)) {
    return connectors.get(chatId)!;
  }

  const connector = new TonConnect({
    manifestUrl: process.env.MANIFEST_URL!,
    storage: new TonConnectStorage(chatId)
  });

  connectors.set(chatId, connector);
  return connector;
}
