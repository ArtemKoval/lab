import mongoose, { Schema } from 'mongoose'
const ObjectId = mongoose.Schema.Types.ObjectId

const paymentSchema = new Schema({
  status: {
    type: String
  },
  order_id: {
    type: ObjectId
  }
}, {
  timestamps: true,
  toJSON: {
    virtuals: true,
    transform: (obj, ret) => { delete ret._id }
  }
})

paymentSchema.methods = {
  view (full) {
    const view = {
      // simple view
      id: this.id,
      status: this.status,
      order_id: this.order_id,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    }

    return full ? {
      ...view
      // add properties for a full view
    } : view
  }
}

const model = mongoose.model('Payment', paymentSchema)

export const schema = model.schema
export default model
