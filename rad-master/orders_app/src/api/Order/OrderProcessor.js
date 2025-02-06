const rp = require('request-promise')

class OrderProcessor {
  makePaymentRequest (options, order) {
    return new Promise((resolve, reject) => {
      options.body = {order_id: order._id}
      rp(options)
        .then(resolve)
        .catch((err) => {
          reject(err)
        })
    })
  }
}

export default OrderProcessor
