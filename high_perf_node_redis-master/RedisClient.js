const uuidv4 = require('uuid/v4');
const redis = require('redis');
const {promisify} = require('util');

class RedisClient {
    constructor(options) {
        options = options || {};

        this.client = redis.createClient({
            host: options.host || '127.0.0.1',
            port: options.port || 6379,
            url: options.url || null
        });

        this.delayedListName = 'delayed';
        this.queueListName = 'queue';

        this.get = promisify(this.client.get).bind(this.client);
        this.setnx = promisify(this.client.setnx).bind(this.client);
        this.expire = promisify(this.client.expire).bind(this.client);
        this.zadd = promisify(this.client.zadd).bind(this.client);
        this.zrem = promisify(this.client.zrem).bind(this.client);
        this.lpop = promisify(this.client.lpop).bind(this.client);
        this.rpush = promisify(this.client.rpush).bind(this.client);
        this.zrange = promisify(this.client.zrange).bind(this.client);
        this.watch = promisify(this.client.watch).bind(this.client);
        this.unwatch = promisify(this.client.unwatch).bind(this.client);
        this.multi = promisify(this.client.multi).bind(this.client);
        this.del = promisify(this.client.del).bind(this.client);
        this.exec = promisify(this.client.exec).bind(this.client);
        this.quit = promisify(this.client.quit).bind(this.client);
    }

    async addToDelayedList(item, score) {
        return await this.zadd(this.delayedListName, 'NX', score, item);
    }

    async getFromDelayedList() {
        return await this.zrange(this.delayedListName, 0, 0, 'WITHSCORES');
    }

    async removeFromDelayedList(item) {
        return await this.zrem(this.delayedListName, item);
    }

    async addToQueueList(item) {
        return await this.rpush(this.queueListName, item);
    }

    async getFromQueueList() {
        return await this.lpop(this.queueListName);
    }

    async acquireLock(key, ttlSec = 10) {
        const lockName = `lock_${key}`;
        const lockId = uuidv4();
        if (await this.setnx(lockName, lockId)) {
            await this.expire(lockName, ttlSec);
            return lockId;
        }
        return null;
    }

    async releaseLock(id, lockId) {
        const lockName = `lock_${id}`;
        await this.watch(lockName);
        if (await this.get(lockName) === lockId) {
            await this.del(lockName);
            return true;
        }
        await this.unwatch();
        return false;
    }
}

module.exports = RedisClient;