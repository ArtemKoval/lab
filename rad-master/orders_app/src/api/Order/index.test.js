/* eslint-disable import/first,camelcase */
jest.mock('./OrderProcessor', () => {
  return jest.fn().mockImplementation(() => {
    return {
      makePaymentRequest: () => {
        return Promise.resolve({
          order_id: '5cd2c4fa48a289e465fff0a2',
          _id: '5cd2c4fa48a289e465fff0a2',
          status: 'confirmed'
        })
      }
    }
  })
})

jest.mock('./OrderProcessor')

import request from 'supertest'
import {apiRoot} from '../../config'
import express from '../../services/express'
import routes, {Order} from '.'

const app = () => express(apiRoot, routes)

let order

beforeEach(async () => {
  order = await Order.create({
    _id: '5cd2c4fa48a289e465fff0a2',
    user_id: '5cd2c4fa48a289e465fff0a2',
    status: 'created'
  })
})

test('POST /Orders 201 Order must be created with "created" status', async () => {
  const {status, body} = await request(app())
    .post(`${apiRoot}`)
    .send({
      status: 'wrong_status',
      user_id: '5cd2c4fa48a289e465fff0a2'
    })
  expect(status).toBe(201)
  expect(typeof body).toEqual('object')
  expect(body.status).toEqual('confirmed')
  expect(body.user_id).toEqual('5cd2c4fa48a289e465fff0a2')
})

test('GET /Orders 200', async () => {
  const {status, body} = await request(app())
    .get(`${apiRoot}`)
  expect(status).toBe(200)
  expect(Array.isArray(body)).toBe(true)
})

test('GET /Orders/:id 200', async () => {
  const {status, body} = await request(app())
    .get(`${apiRoot}/${order.id}`)
  expect(status).toBe(200)
  expect(typeof body).toEqual('object')
  expect(body.id).toEqual(order.id)
})

test('GET /Orders/:id 404', async () => {
  const {status} = await request(app())
    .get(apiRoot + '/123456789098765432123456')
  expect(status).toBe(404)
})

test('PUT /Orders/:id 200', async () => {
  const {status, body} = await request(app())
    .put(`${apiRoot}/${order.id}`)
    .send({
      status: 'test',
      user_id: '5cd2c4fa48a289e465fff0b4',
      payment_id: '5cd2c4fa48a289e465fff0b4'
    })
  expect(status).toBe(200)
  expect(typeof body).toEqual('object')
  expect(body.id).toEqual(order.id)
  expect(body.status).toEqual('test')
  expect(body.user_id).toEqual('5cd2c4fa48a289e465fff0b4')
  expect(body.payment_id).toEqual('5cd2c4fa48a289e465fff0b4')
})

test('PUT /Orders/:id 404', async () => {
  const {status} = await request(app())
    .put(apiRoot + '/123456789098765432123456')
    .send({status: 'test', user_id: 'test', payment_id: 'test'})
  expect(status).toBe(404)
})

test('DELETE /Orders/:id 204', async () => {
  const {status} = await request(app())
    .delete(`${apiRoot}/${order.id}`)
  expect(status).toBe(204)
})

test('DELETE /Orders/:id 404', async () => {
  const {status} = await request(app())
    .delete(apiRoot + '/123456789098765432123456')
  expect(status).toBe(404)
})
