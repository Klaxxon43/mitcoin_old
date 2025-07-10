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
exports.TonConnectStorage = void 0;
const ioredis_1 = __importDefault(require("ioredis"));
const redis = new ioredis_1.default('//localhost:6379'); // подключение к Redis
class TonConnectStorage {
    constructor(chatId) {
        this.chatId = chatId;
    }
    getKey(key) {
        return `tonconnect:${this.chatId}:${key}`;
    }
    removeItem(key) {
        return __awaiter(this, void 0, void 0, function* () {
            yield redis.del(this.getKey(key));
        });
    }
    setItem(key, value) {
        return __awaiter(this, void 0, void 0, function* () {
            yield redis.set(this.getKey(key), value);
        });
    }
    getItem(key) {
        return __awaiter(this, void 0, void 0, function* () {
            return yield redis.get(this.getKey(key));
        });
    }
}
exports.TonConnectStorage = TonConnectStorage;
//# sourceMappingURL=storage.js.map