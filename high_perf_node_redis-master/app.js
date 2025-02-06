const DelayedProcessor = require('./DelayedProcessor');

(async () => {
    'use strict';

    const processor = new DelayedProcessor();
    await processor.pool();


})().catch((e) => {
    'use strict';
    console.error(`[app] Crashed with error - ${e.message}\n${e.stack}`);
    process.exit(-1);
});
