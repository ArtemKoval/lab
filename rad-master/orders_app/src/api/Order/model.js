import mongoose, { Schema } from 'mongoose'
const ObjectId = mongoose.Schema.Types.ObjectId

const orderSchema = new Schema({
  status: {
    type: String
  },
  user_id: {
    type: ObjectId
  },
  payment_id: {
    type: ObjectId
  }
}, {
  timestamps: true,
  toJSON: {
    virtuals: true,
    transform: (obj, ret) => { delete ret._id }
  }
})

orderSchema.methods = {
  view (full) {
    const view = {
      // simple view
      id: this.id,
      status: this.status,
      user_id: this.user_id,
      payment_id: this.payment_id,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    }

    return full ? {
      ...view
      // add properties for a full view
    } : view
  }
}

const model = mongoose.model('Order', orderSchema)

export const schema = model.schema
export default model
