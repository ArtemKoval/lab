const crypto = require('crypto');
const {promisify} = require('util');
const RedisClient = require('./RedisClient');

class DelayedProcessor {
    constructor() {
        this.client = new RedisClient();
        this.queueTimeoutMs = 50;
        this.setTimeoutPromise = promisify(setTimeout);
    }

    async executeLater(message, delay) {
        const now = new Date().getTime();
        const id = DelayedProcessor.getId(message);
        const item = JSON.stringify({message, id});
        const score = parseFloat(now + delay);
        let status = await this.client.addToDelayedList(item, score);
        return {status, id};
    }

    async pool() {
        await this.setTimeoutPromise(this.queueTimeoutMs).then(async () => {
            await this.poolDelayedProcess();
            await this.poolQueueProcess();
            await this.pool();
        });
    }

    async poolQueueProcess() {
        const item = await this.client.getFromQueueList();
        if (!item)
            return;

        console.log('---------');
        console.log(item);
        console.log('---------');
    }

    static getId(message) {
        return crypto.createHash('md5').update(message).digest('hex');
    }

    async poolDelayedProcess() {
        const now = new Date().getTime();
        let item = await this.client.getFromDelayedList();

        if (!item || item.length === 0)
            return null;
        const targetDate = parseFloat(item[1]);
        if (targetDate > now)
            return null;

        item = item[0];

        try {
            JSON.parse(item);
        } catch (e) {
            console.error(`Cant parse '${item}' json. Removing it from delayed queue.`);
            await this.client.removeFromDelayedList(item);
            return;
        }

        const {message, id} = JSON.parse(item);
        const lockId = await this.client.acquireLock(id);
        //console.log(`Acquiring: ${lockId}`);
        if (!lockId)
            return null;

        if (await this.client.removeFromDelayedList(item))
            await this.client.addToQueueList(item);

        const success = await this.client.releaseLock(id, lockId);
        //console.log(`Releasing: ${success}`);
    }
}

module.exports = DelayedProcessor;