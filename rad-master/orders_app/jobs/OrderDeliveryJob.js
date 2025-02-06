import {deliveredTimeoutInSec} from '../src/config'
import Order from '../src/api/Order/model'
import {Statuses} from '../src/api/Order/OrderStatuses'

class OrderDeliveryJob {
  static register () {
    setInterval(() => {
      console.log('Deliver confirmed orders job')
      Order.find({status: Statuses.CONFIRMED})
        .then((orders) => {
          console.log(JSON.stringify(orders))
          orders.forEach((order) => {
            Object.assign(order,
              {
                status: Statuses.DELIVERED
              }).save()
          })
        })
    }, deliveredTimeoutInSec * 1000).unref()
  }
}

export default OrderDeliveryJob
