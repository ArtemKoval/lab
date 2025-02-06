import {Payment} from './index'

class PaymentService {
  constructor () {
    this.statuses = ['confirmed', 'declined']
  }

  processOrder (body) {
    return new Promise((resolve, reject) => {
      body.status = this.statuses[Math.floor(Math.random() * this.statuses.length)]
      Payment.create(body)
        .then(resolve)
        .catch(reject)
    })
  }
}

export default PaymentService
