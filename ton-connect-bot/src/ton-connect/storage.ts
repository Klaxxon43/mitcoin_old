// src/ton-connect/storage.ts
import { IStorage } from '@tonconnect/sdk';
import Redis from 'ioredis';

const redis = new Redis('//localhost:6379'); // подключение к Redis

export class TonConnectStorage implements IStorage {
  constructor(private readonly chatId: number) {}

  private getKey(key: string): string {
    return `tonconnect:${this.chatId}:${key}`;
  }

  async removeItem(key: string): Promise<void> {
    await redis.del(this.getKey(key));
  }

  async setItem(key: string, value: string): Promise<void> {
    await redis.set(this.getKey(key), value);
  }

  async getItem(key: string): Promise<string | null> {
    return await redis.get(this.getKey(key));
  }
}
