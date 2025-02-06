# Java Script Fullstack

## Quick start

I. Clone this repo

II. Launch microservices

 ```bash
    docker-compose up
```

III. Stop microservices

```bash
   docker-compose down
```

IV. Sample request

```bash
    curl -X POST \
      http://localhost:4242/orders \
      -H 'Content-Type: application/json' \
      -d '{
    	"user_id": "5cd2c4fa48a234e465fff023"
    }'
```

V. Sample response

```json
    {
        "id": "5cd422f0693e9405a5d2d012",
        "status": "confirmed",
        "user_id": "5cd2c4fa48a234e465fff023",
        "payment_id": "5cd422f05e07b500cdab6d1b",
        "createdAt": "2019-05-09T12:54:08.130Z",
        "updatedAt": "2019-05-09T12:54:08.154Z"
    }
```

## Technology choices

### ExpressJS + Node

As specified per the original requirement.

I used generator to https://github.com/diegohaz/rest ensure code cohesiveness and concentrate on business logic and devops.


### MongoDB

A natural NoSQL companion choice


### Docker

A modern way to develop & deploy microservices

### Language

I decided to go with a pure ES6 + transpilation via Babel. Another strong choice is to go Typescript in the whole stack.

Promises are wrapped via Bluebird package.

For the tests I used Jest which is the de-facto testing framework at the moment.

## Architecture

Per project specifications there are two microservices.

orders_app is responsible for managing orders.

payments_app is responsible for abstracting payment processing.

Flow is specified in the original pdf document.

### Trade-offs, extension points

Each service has both unit tests and integration (e2e) tests. They are located in ./src/api/Payment and ./src/api/Order folders. More test could be added to cover additional scenarios.

The job responsible for moving Orders to 'delivered' state is located in orders_app/jobs/OrderDeliverJobs.js file. It's attached to the process inside src/app.js. In the real application all of such jobs should be moved into a separate service application (ideally to something like AWS Lambda).

Right now services are communicating directly. For the real live scenario queues must seperate them (like AWS SQS, Kinesis).

Depending on the overall needs and timeline it may be possible to use a single DB for each microservices. Which helps with reporting down the road (if a project does not have time to setup a data ingestion system).

I left the UI off because of the time-constraint.

For the real project with much more microservices it makes sense to move business logic into one or more separate projects (packages).

## Development tasks for each microservice

Each microservices has useful tasks defined in package.json, some of them are:

```bash
npm test # test using Jest
npm run coverage # test and open the coverage report in the browser
npm run lint # lint using ESLint
npm run dev # run the API in development mode
npm run prod # run the API in production mode
npm run docs # generate API docs
```
