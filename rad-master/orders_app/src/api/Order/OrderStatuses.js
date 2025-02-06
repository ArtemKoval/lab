const enumValue = (name) => Object.freeze({toString: () => name})

const OrderStatuses = Object.freeze({
  CREATED: enumValue('created'),
  CONFIRMED: enumValue('confirmed'),
  DELIVERED: enumValue('delivered'),
  CANCELED: enumValue('canceled')
})

export const Statuses = OrderStatuses
