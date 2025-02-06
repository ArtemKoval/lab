/* eslint-disable import/first */
jest.mock('request-promise')

import rp from 'request-promise'
import request from 'supertest'
import {apiRoot} from '../../config'
import express from '../../services/express'
import routes, {Payment} from '.'

const app = () => express(apiRoot, routes)

let payment

beforeEach(async () => {
  payment = await Payment.create({})
})

test('POST /Payments 201', async () => {
  rp.mockReturnValue(Promise.resolve({}))
  const {status, body} = await request(app())
    .post(`${apiRoot}`)
    .send(
      {
        status: 'test',
        order_id: '5cd2c4fa48a234e465fff022'
      })
  expect(status).toBe(201)
  expect(typeof body).toEqual('object')
  expect(['confirmed', 'declined']).toContain(body.status)
  expect(body.order_id).toEqual('5cd2c4fa48a234e465fff022')
})

test('GET /Payments 200', async () => {
  const {status, body} = await request(app())
    .get(`${apiRoot}`)
  expect(status).toBe(200)
  expect(Array.isArray(body)).toBe(true)
})

test('GET /Payments/:id 200', async () => {
  const {status, body} = await request(app())
    .get(`${apiRoot}/${payment.id}`)
  expect(status).toBe(200)
  expect(typeof body).toEqual('object')
  expect(body.id).toEqual(payment.id)
})

test('GET /Payments/:id 404', async () => {
  const {status} = await request(app())
    .get(apiRoot + '/123456789098765432123456')
  expect(status).toBe(404)
})

test('PUT /Payments/:id 200', async () => {
  const {status, body} = await request(app())
    .put(`${apiRoot}/${payment.id}`)
    .send({
      status: 'test',
      order_id: '5cd2c4fa48a234e465fff033'
    })
  expect(status).toBe(200)
  expect(typeof body).toEqual('object')
  expect(body.id).toEqual(payment.id)
  expect(body.status).toEqual('test')
  expect(body.order_id).toEqual('5cd2c4fa48a234e465fff033')
})

test('PUT /Payments/:id 404', async () => {
  const {status} = await request(app())
    .put(apiRoot + '/123456789098765432123456')
    .send({status: 'test', order_id: 'test'})
  expect(status).toBe(404)
})

test('DELETE /Payments/:id 204', async () => {
  const {status} = await request(app())
    .delete(`${apiRoot}/${payment.id}`)
  expect(status).toBe(204)
})

test('DELETE /Payments/:id 404', async () => {
  const {status} = await request(app())
    .delete(apiRoot + '/123456789098765432123456')
  expect(status).toBe(404)
})
