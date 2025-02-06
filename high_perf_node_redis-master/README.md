Start:
$ node web.js
or
$ PORT=7000 node web.js

Test work:
$ curl -X POST "http://127.0.0.1:3000/" -H "Content-Type: application/json" -d "{\"message\":\"lorem ipsum\",\"delay\":5000}"