import {Payment} from '.'

let payment

beforeEach(async () => {
  payment = await Payment.create({
    status: 'test',
    order_id: '5cd2c4fa48a234e465fff022'
  })
})

describe('view', () => {
  it('returns simple view', () => {
    const view = payment.view()
    expect(typeof view).toBe('object')
    expect(view.id).toBe(payment.id)
    expect(view.status).toBe(payment.status)
    expect(view.order_id).toBe(payment.order_id)
    expect(view.createdAt).toBeTruthy()
    expect(view.updatedAt).toBeTruthy()
  })

  it('returns full view', () => {
    const view = payment.view(true)
    expect(typeof view).toBe('object')
    expect(view.id).toBe(payment.id)
    expect(view.status).toBe(payment.status)
    expect(view.order_id).toBe(payment.order_id)
    expect(view.createdAt).toBeTruthy()
    expect(view.updatedAt).toBeTruthy()
  })
})
