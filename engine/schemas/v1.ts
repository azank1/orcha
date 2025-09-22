/**
 * v1 Schema Definitions for MCP Tools
 * 
 * TODO: Define TypeBox schemas for the three tools (req/res) with shared models 
 * (Money, Line, OrderDraft, Issue, RequestMeta).
 * 
 * Rules: 
 * - strict types, required vs optional
 * - pagination (page, page_size)
 * - search (q)
 * - forbid unknown fields at validation time later
 */

import { Type, Static } from '@sinclair/typebox'

// ============================================================================
// SHARED MODELS
// ============================================================================

/**
 * Money representation with currency and amount
 */
export const Money = Type.Object({
  currency: Type.String({ 
    minLength: 3, 
    maxLength: 3,
    pattern: "^[A-Z]{3}$",
    description: "ISO 4217 currency code (e.g., USD, EUR)"
  }),
  amount: Type.Number({ 
    minimum: 0,
    description: "Amount in the smallest currency unit (e.g., cents)"
  })
}, {
  additionalProperties: false,
  description: "Monetary value with currency"
})

/**
 * Order line item
 */
export const Line = Type.Object({
  sku: Type.String({ 
    minLength: 1,
    description: "Product SKU identifier"
  }),
  qty: Type.Integer({ 
    minimum: 1,
    description: "Quantity of items"
  }),
  note: Type.Optional(Type.String({
    maxLength: 500,
    description: "Optional item notes or modifications"
  }))
}, {
  additionalProperties: false,
  description: "Order line item"
})

/**
 * Request metadata for tracking and idempotency
 */
export const RequestMeta = Type.Object({
  request_id: Type.Optional(Type.String({
    minLength: 1,
    description: "Optional request tracking ID"
  })),
  idem: Type.Optional(Type.String({
    minLength: 8,
    maxLength: 64,
    description: "Idempotency key for duplicate prevention"
  }))
}, {
  additionalProperties: false,
  description: "Request metadata"
})

/**
 * Validation issue
 */
export const Issue = Type.Object({
  code: Type.String({
    minLength: 1,
    description: "Error code identifier"
  }),
  message: Type.String({
    minLength: 1,
    description: "Human-readable error message"
  }),
  field: Type.Optional(Type.String({
    description: "Field name that caused the issue"
  }))
}, {
  additionalProperties: false,
  description: "Validation or business rule issue"
})

/**
 * Order draft with calculated totals
 */
export const OrderDraft = Type.Object({
  items: Type.Array(Line, {
    minItems: 1,
    description: "Order line items"
  }),
  subtotal: Money,
  taxes: Type.Array(Money, {
    description: "Tax breakdown"
  }),
  fees: Type.Array(Money, {
    description: "Additional fees (delivery, service, etc.)"
  }),
  total: Money,
  promos: Type.Optional(Type.Array(Type.String(), {
    description: "Applied promotion codes"
  }))
}, {
  additionalProperties: false,
  description: "Order draft with calculated pricing"
})

// ============================================================================
// MENU.EXPORT SCHEMAS
// ============================================================================

export const MenuExportReq = Type.Intersect([
  RequestMeta,
  Type.Object({
    store_id: Type.Optional(Type.String({
      minLength: 1,
      description: "Store identifier filter"
    })),
    page: Type.Optional(Type.Integer({
      minimum: 1,
      default: 1,
      description: "Page number for pagination"
    })),
    page_size: Type.Optional(Type.Integer({
      minimum: 1,
      maximum: 200,
      default: 50,
      description: "Items per page"
    })),
    q: Type.Optional(Type.String({
      maxLength: 100,
      description: "Search query for menu items"
    }))
  }, {
    additionalProperties: false
  })
], {
  description: "Menu export request"
})

export const MenuItem = Type.Object({
  sku: Type.String({
    minLength: 1,
    description: "Product SKU"
  }),
  name: Type.String({
    minLength: 1,
    maxLength: 200,
    description: "Item name"
  }),
  desc: Type.Optional(Type.String({
    maxLength: 1000,
    description: "Item description"
  })),
  price: Money,
  available: Type.Boolean({
    description: "Availability status"
  }),
  tags: Type.Optional(Type.Array(Type.String(), {
    description: "Item tags (vegetarian, spicy, etc.)"
  })),
  category: Type.String({
    minLength: 1,
    description: "Category identifier"
  })
}, {
  additionalProperties: false,
  description: "Menu item"
})

export const MenuCategory = Type.Object({
  id: Type.String({
    minLength: 1,
    description: "Category identifier"
  }),
  name: Type.String({
    minLength: 1,
    maxLength: 100,
    description: "Category display name"
  })
}, {
  additionalProperties: false,
  description: "Menu category"
})

export const MenuExportRes = Type.Object({
  menu: Type.Object({
    categories: Type.Array(MenuCategory, {
      description: "Available categories"
    }),
    items: Type.Array(MenuItem, {
      description: "Menu items"
    })
  }, {
    additionalProperties: false
  }),
  page: Type.Integer({
    minimum: 1,
    description: "Current page number"
  }),
  page_size: Type.Integer({
    minimum: 1,
    description: "Items per page"
  }),
  total: Type.Integer({
    minimum: 0,
    description: "Total number of items"
  })
}, {
  additionalProperties: false,
  description: "Menu export response"
})

// ============================================================================
// ORDER.VALIDATE SCHEMAS
// ============================================================================

export const Customer = Type.Object({
  mode: Type.Union([
    Type.Literal('PICKUP'),
    Type.Literal('DELIVERY')
  ], {
    description: "Order fulfillment mode"
  }),
  name: Type.Optional(Type.String({
    minLength: 1,
    maxLength: 100,
    description: "Customer name"
  })),
  phone: Type.Optional(Type.String({
    pattern: "^\\+?[1-9]\\d{1,14}$",
    description: "Customer phone number (E.164 format)"
  })),
  address: Type.Optional(Type.String({
    maxLength: 500,
    description: "Delivery address (required for DELIVERY mode)"
  }))
}, {
  additionalProperties: false,
  description: "Customer information"
})

export const PaymentHint = Type.Object({
  method: Type.Union([
    Type.Literal('CARD'),
    Type.Literal('CASH'),
    Type.Literal('NONE')
  ], {
    description: "Intended payment method"
  })
}, {
  additionalProperties: false,
  description: "Payment method hint"
})

export const OrderValidateReq = Type.Intersect([
  RequestMeta,
  Type.Object({
    store_id: Type.String({
      minLength: 1,
      description: "Target store identifier"
    }),
    items: Type.Array(Line, {
      minItems: 1,
      description: "Order items to validate"
    }),
    customer: Customer,
    payment: Type.Optional(PaymentHint)
  }, {
    additionalProperties: false
  })
], {
  description: "Order validation request"
})

export const OrderValidateRes = Type.Object({
  ok: Type.Boolean({
    description: "Validation success status"
  }),
  draft: Type.Optional(OrderDraft),
  issues: Type.Optional(Type.Array(Issue, {
    description: "Validation issues (if any)"
  }))
}, {
  additionalProperties: false,
  description: "Order validation response"
})

// ============================================================================
// ORDER.ACCEPT SCHEMAS
// ============================================================================

export const OrderAcceptReq = Type.Intersect([
  RequestMeta,
  Type.Object({
    store_id: Type.String({
      minLength: 1,
      description: "Target store identifier"
    }),
    draft: OrderDraft
  }, {
    additionalProperties: false
  })
], {
  description: "Order acceptance request"
})

export const OrderAcceptRes = Type.Object({
  ok: Type.Boolean({
    description: "Order acceptance status"
  }),
  order_id: Type.String({
    minLength: 1,
    description: "Generated order identifier"
  }),
  eta: Type.Optional(Type.String({
    pattern: "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$",
    description: "Estimated completion time (ISO 8601 format)"
  })),
  idem: Type.String({
    minLength: 8,
    description: "Idempotency key used for this order"
  })
}, {
  additionalProperties: false,
  description: "Order acceptance response"
})

// ============================================================================
// EXPORTED TYPES
// ============================================================================

export type TMenuExportReq = Static<typeof MenuExportReq>
export type TMenuExportRes = Static<typeof MenuExportRes>
export type TOrderValidateReq = Static<typeof OrderValidateReq>
export type TOrderValidateRes = Static<typeof OrderValidateRes>
export type TOrderAcceptReq = Static<typeof OrderAcceptReq>
export type TOrderAcceptRes = Static<typeof OrderAcceptRes>

// Shared types
export type TMoney = Static<typeof Money>
export type TLine = Static<typeof Line>
export type TOrderDraft = Static<typeof OrderDraft>
export type TIssue = Static<typeof Issue>
export type TCustomer = Static<typeof Customer>
export type TMenuItem = Static<typeof MenuItem>