import { Router } from 'express'
import { middleware as query } from 'querymen'
import { middleware as body } from 'bodymen'
import { create, index, show, update, destroy } from './controller'
import { schema } from './model'
export Order, { schema } from './model'

const router = new Router()
const { status, user_id, payment_id } = schema.tree

/**
 * @api {post} /Orders Create order
 * @apiName CreateOrder
 * @apiGroup Order
 * @apiParam status Order's status.
 * @apiParam user_id Order's user_id.
 * @apiParam payment_id Order's payment_id.
 * @apiSuccess {Object} order Order's data.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 * @apiError 404 Order not found.
 */
router.post('/',
  body({ status, user_id, payment_id }),
  create)

/**
 * @api {get} /Orders Retrieve orders
 * @apiName RetrieveOrders
 * @apiGroup Order
 * @apiUse listParams
 * @apiSuccess {Object[]} orders List of orders.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 */
router.get('/',
  query(),
  index)

/**
 * @api {get} /Orders/:id Retrieve order
 * @apiName RetrieveOrder
 * @apiGroup Order
 * @apiSuccess {Object} order Order's data.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 * @apiError 404 Order not found.
 */
router.get('/:id',
  show)

/**
 * @api {put} /Orders/:id Update order
 * @apiName UpdateOrder
 * @apiGroup Order
 * @apiParam status Order's status.
 * @apiParam user_id Order's user_id.
 * @apiParam payment_id Order's payment_id.
 * @apiSuccess {Object} order Order's data.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 * @apiError 404 Order not found.
 */
router.put('/:id',
  body({ status, user_id, payment_id }),
  update)

/**
 * @api {delete} /Orders/:id Delete order
 * @apiName DeleteOrder
 * @apiGroup Order
 * @apiSuccess (Success 204) 204 No Content.
 * @apiError 404 Order not found.
 */
router.delete('/:id',
  destroy)

export default router
