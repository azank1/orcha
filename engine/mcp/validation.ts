/**
 * Schema validation module for MCP server
 * 
 * Provides TypeBox schema validation with JSON-RPC error formatting
 */

import { TSchema } from '@sinclair/typebox'
import { Value } from '@sinclair/typebox/value'
import { 
  MenuExportReq,
  MenuExportRes,
  OrderValidateReq,
  OrderValidateRes,
  OrderAcceptReq,
  OrderAcceptRes
} from '../schemas/v1.js'

// JSON-RPC error structure
interface JsonRpcError {
  code: number
  message: string
  data?: any
}

/**
 * Validation error thrown when schema validation fails
 */
export class ValidationError extends Error {
  public readonly jsonRpcError: JsonRpcError

  constructor(errors: any[]) {
    const message = "Invalid params"
    super(message)
    this.name = "ValidationError"
    this.jsonRpcError = {
      code: -32602,
      message,
      data: errors
    }
  }
}

/**
 * Assert that data is valid against the given schema
 * Throws ValidationError with JSON-RPC error format on failure
 */
export function assertValid<T extends TSchema>(schema: T, data: unknown): asserts data is typeof schema {
  const errors = [...Value.Errors(schema, data)]
  
  if (errors.length > 0) {
    const formattedErrors = errors.map(error => ({
      path: error.path,
      message: error.message,
      value: error.value
    }))
    
    throw new ValidationError(formattedErrors)
  }
}

/**
 * Validate data against schema and return boolean result
 */
export function isValid<T extends TSchema>(schema: T, data: unknown): data is typeof schema {
  return Value.Check(schema, data)
}

/**
 * Schema registry for easy access to compiled schemas
 */
export const schemas = {
  // Menu schemas
  'menu.export.req': MenuExportReq,
  'menu.export.res': MenuExportRes,
  
  // Order validation schemas
  'order.validate.req': OrderValidateReq,
  'order.validate.res': OrderValidateRes,
  
  // Order acceptance schemas
  'order.accept.req': OrderAcceptReq,
  'order.accept.res': OrderAcceptRes
} as const

export type SchemaName = keyof typeof schemas

/**
 * Get schema by name
 */
export function getSchema(name: SchemaName): TSchema {
  return schemas[name]
}

/**
 * Validate request parameters for a specific tool
 */
export function validateToolRequest(toolName: string, params: unknown): void {
  const schemaName = `${toolName}.req` as SchemaName
  const schema = schemas[schemaName]
  
  if (!schema) {
    throw new ValidationError([{
      path: '/tool',
      message: `Unknown tool: ${toolName}`,
      value: toolName
    }])
  }
  
  assertValid(schema, params)
}

/**
 * Validate response data for a specific tool
 */
export function validateToolResponse(toolName: string, data: unknown): void {
  const schemaName = `${toolName}.res` as SchemaName
  const schema = schemas[schemaName]
  
  if (!schema) {
    throw new ValidationError([{
      path: '/tool',
      message: `Unknown tool: ${toolName}`,
      value: toolName
    }])
  }
  
  assertValid(schema, data)
}