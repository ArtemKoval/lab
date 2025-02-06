import http from 'http'
import {env, port, mongo, ip, apiRoot} from './config'
import express from './services/express'
import api from './api'
import mongoose from './services/mongoose'
import OrderDeliveryJob from '../jobs/OrderDeliveryJob'

const app = express(apiRoot, api)
const server = http.createServer(app)

mongoose.connect(mongo.uri)
mongoose.Promise = Promise

setImmediate(() => {
  server.listen(port, ip, () => {
    console.log('Express server listening on http://%s:%d, in %s mode', ip, port, env)
  })
})

setImmediate(() => {
  OrderDeliveryJob.register()
})

export default app
