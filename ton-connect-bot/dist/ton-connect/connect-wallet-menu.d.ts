import { CallbackQuery } from 'node-telegram-bot-api';
export declare const walletMenuCallbacks: {
    choose_wallet: typeof onChooseWalletClick;
    select_wallet: typeof onWalletClick;
    universal_qr: typeof onOpenUniversalQRClick;
};
declare function onChooseWalletClick(query: CallbackQuery): Promise<void>;
declare function onOpenUniversalQRClick(query: CallbackQuery): Promise<void>;
declare function onWalletClick(query: CallbackQuery, appName: string): Promise<void>;
export {};
