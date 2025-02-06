import {Statuses} from './OrderStatuses'
import {Order} from './index'
import Processor from './OrderProcessor'
import {paymentsAppURI} from '../../config'

class OrderService {
  constructor () {
    this.orderProcessor = new Processor()
  }

  create (body) {
    body.status = Statuses.CREATED
    return Order.create(body)
      .then((order) => {
        let options = {
          method: 'POST',
          uri: paymentsAppURI,
          body: {
            body
          },
          json: true
        }
        return this.orderProcessor.makePaymentRequest(options, order)
      })
      .then((paymentResponse) => {
        let orderStatus = Statuses.CREATED
        switch (paymentResponse.status) {
          case 'declined':
            orderStatus = Statuses.CANCELED
            break
          case 'confirmed':
            orderStatus = Statuses.CONFIRMED
            break
          default:
            throw new Error(`Unknown payment status ${JSON.stringify(paymentResponse)}`)
        }
        return new Promise((resolve, reject) => {
          Order.findById(paymentResponse.order_id)
            .then((order) => order ? Object.assign(order,
              {
                payment_id: paymentResponse.id,
                status: orderStatus
              }).save() : null)
            .then(resolve)
            .catch((err) => {
              reject(err)
            })
        })
      })
      .catch((err) => {
        throw new Error(err)
      })
  }
}

export default OrderService
