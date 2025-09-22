/**
 * COPILOT TASK: Create v1 JSON Schemas for MCP tools (TypeBox) and emit compiled JSON.
 * Acceptance criteria:
 * - Tools: menu.export, order.validate, order.accept.
 * - Request/response TypeBox schemas defined with minimal but strict fields.
 * - Export TS types and compile to plain JSON under schemas/json/*.json via a small build script.
 * - Unknown fields must be rejected at validation time.
 */
import { Type, Static } from '@sinclair/typebox'

// Shared
export const Money = Type.Object({ 
  currency: Type.String({ minLength: 3, maxLength: 3 }), 
  amount: Type.Number({ minimum: 0 }) 
})

export const Line = Type.Object({ 
  sku: Type.String(), 
  qty: Type.Integer({ minimum: 1 }), 
  note: Type.Optional(Type.String()) 
})

export const RequestMeta = Type.Object({ 
  request_id: Type.Optional(Type.String()), 
  idem: Type.Optional(Type.String({ minLength: 8 })) 
})

// menu.export
export const MenuExportReq = Type.Intersect([RequestMeta, Type.Object({
  store_id: Type.Optional(Type.String()),
  page: Type.Optional(Type.Integer({ minimum: 1 })),
  page_size: Type.Optional(Type.Integer({ minimum: 1, maximum: 200 })),
  q: Type.Optional(Type.String()),
})])

export const MenuItem = Type.Object({ 
  sku: Type.String(), 
  name: Type.String(), 
  desc: Type.Optional(Type.String()), 
  price: Money, 
  available: Type.Boolean(), 
  tags: Type.Optional(Type.Array(Type.String())), 
  category: Type.String() 
})

export const MenuExportRes = Type.Object({ 
  menu: Type.Object({ 
    categories: Type.Array(Type.Object({ 
      id: Type.String(), 
      name: Type.String() 
    })), 
    items: Type.Array(MenuItem) 
  }), 
  page: Type.Integer(), 
  page_size: Type.Integer(), 
  total: Type.Integer() 
})

// order.validate
export const Customer = Type.Object({ 
  mode: Type.Union([Type.Literal('PICKUP'), Type.Literal('DELIVERY')]), 
  name: Type.Optional(Type.String()), 
  phone: Type.Optional(Type.String()), 
  address: Type.Optional(Type.String()) 
})

export const PaymentHint = Type.Object({ 
  method: Type.Union([Type.Literal('CARD'), Type.Literal('CASH'), Type.Literal('NONE')]) 
})

export const OrderValidateReq = Type.Intersect([RequestMeta, Type.Object({ 
  store_id: Type.String(), 
  items: Type.Array(Line, { minItems: 1 }), 
  customer: Customer, 
  payment: Type.Optional(PaymentHint) 
})])

export const Issue = Type.Object({ 
  code: Type.String(), 
  message: Type.String(), 
  field: Type.Optional(Type.String()) 
})

export const OrderDraft = Type.Object({ 
  items: Type.Array(Line), 
  subtotal: Money, 
  taxes: Type.Array(Money), 
  fees: Type.Array(Money), 
  total: Money, 
  promos: Type.Optional(Type.Array(Type.String())) 
})

export const OrderValidateRes = Type.Object({ 
  ok: Type.Boolean(), 
  draft: Type.Optional(OrderDraft), 
  issues: Type.Optional(Type.Array(Issue)) 
})

// order.accept
export const OrderAcceptReq = Type.Intersect([RequestMeta, Type.Object({ 
  store_id: Type.String(), 
  draft: OrderDraft 
})])

export const OrderAcceptRes = Type.Object({ 
  ok: Type.Boolean(), 
  order_id: Type.String(), 
  eta: Type.Optional(Type.String()), 
  idem: Type.String() 
})

// Exported TypeScript types
export type TMenuExportReq = Static<typeof MenuExportReq>
export type TMenuExportRes = Static<typeof MenuExportRes>
export type TOrderValidateReq = Static<typeof OrderValidateReq>
export type TOrderValidateRes = Static<typeof OrderValidateRes>
export type TOrderAcceptReq = Static<typeof OrderAcceptReq>
export type TOrderAcceptRes = Static<typeof OrderAcceptRes>