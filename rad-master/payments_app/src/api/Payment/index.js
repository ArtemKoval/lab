import { Router } from 'express'
import { middleware as query } from 'querymen'
import { middleware as body } from 'bodymen'
import { create, index, show, update, destroy } from './controller'
import { schema } from './model'
export Payment, { schema } from './model'

const router = new Router()
// eslint-disable-next-line camelcase
const { status, order_id } = schema.tree

/**
 * @api {post} /Payments Create payment
 * @apiName CreatePayment
 * @apiGroup Payment
 * @apiParam status Payment's status.
 * @apiParam order_id Payment's order_id.
 * @apiSuccess {Object} payment Payment's data.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 * @apiError 404 Payment not found.
 */
router.post('/',
  body({ status, order_id }),
  create)

/**
 * @api {get} /Payments Retrieve payments
 * @apiName RetrievePayments
 * @apiGroup Payment
 * @apiUse listParams
 * @apiSuccess {Object[]} payments List of payments.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 */
router.get('/',
  query(),
  index)

/**
 * @api {get} /Payments/:id Retrieve payment
 * @apiName RetrievePayment
 * @apiGroup Payment
 * @apiSuccess {Object} payment Payment's data.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 * @apiError 404 Payment not found.
 */
router.get('/:id',
  show)

/**
 * @api {put} /Payments/:id Update payment
 * @apiName UpdatePayment
 * @apiGroup Payment
 * @apiParam status Payment's status.
 * @apiParam order_id Payment's order_id.
 * @apiSuccess {Object} payment Payment's data.
 * @apiError {Object} 400 Some parameters may contain invalid values.
 * @apiError 404 Payment not found.
 */
router.put('/:id',
  body({ status, order_id }),
  update)

/**
 * @api {delete} /Payments/:id Delete payment
 * @apiName DeletePayment
 * @apiGroup Payment
 * @apiSuccess (Success 204) 204 No Content.
 * @apiError 404 Payment not found.
 */
router.delete('/:id',
  destroy)

export default router
