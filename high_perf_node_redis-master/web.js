const express = require('express');
const bodyParser = require('body-parser');
const DelayedProcessor = require('./DelayedProcessor');

const app = express();
const processor = new DelayedProcessor();
const port = process.env.PORT || 3000;

app.use(bodyParser.json());

app.post('/', (req, res) => {
    console.log(`POST: ${JSON.stringify(req.body)}`);
    processor.executeLater(req.body.message, parseInt(req.body.delay) || 0)
        .then((result) => {
            const status = result.status ? 'queued' : 'ignored';
            console.log(status);
            res.json({status, id: result.id});
        })
        .catch((e) => {
            console.log(e.message);
            res.status(500).json({status: 'error', message: e.message});
        });
});

app.listen(port, () => {
    console.log(`Listening at http://127.0.0.1:${port}/`);
});

(async () => {
    'use strict';
    await processor.pool();
})().catch((e) => {
    'use strict';
    console.error(`DelayedProcessor crashed with error: ${e.message}\n${e.stack}`);
    process.exit(-1);
});
