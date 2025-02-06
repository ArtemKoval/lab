import {Order} from '.'

let order

beforeEach(async () => {
  order = await Order.create({
    status: 'test',
    user_id: '5cd2c4fa48a289e465fff0a2',
    payment_id: '5cd2c4fa48a289e465fff0a5'
  })
})

describe('view', () => {
  it('returns simple view', () => {
    const view = order.view()
    expect(typeof view).toBe('object')
    expect(view.id).toBe(order.id)
    expect(view.status).toBe(order.status)
    expect(view.user_id).toBe(order.user_id)
    expect(view.payment_id).toBe(order.payment_id)
    expect(view.createdAt).toBeTruthy()
    expect(view.updatedAt).toBeTruthy()
  })

  it('returns full view', () => {
    const view = order.view(true)
    expect(typeof view).toBe('object')
    expect(view.id).toBe(order.id)
    expect(view.status).toBe(order.status)
    expect(view.user_id).toBe(order.user_id)
    expect(view.payment_id).toBe(order.payment_id)
    expect(view.createdAt).toBeTruthy()
    expect(view.updatedAt).toBeTruthy()
  })
})
