/**
 * Build script to compile TypeBox schemas to JSON files
 * 
 * TODO: Import schemas/v1.ts, compile the six schemas, and write them to schemas/json/*.json.
 */

import { writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import {
  MenuExportReq,
  MenuExportRes,
  OrderValidateReq,
  OrderValidateRes,
  OrderAcceptReq,
  OrderAcceptRes
} from '../schemas/v1.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const outputDir = join(__dirname, '..', 'schemas', 'json')

// Ensure output directory exists
mkdirSync(outputDir, { recursive: true })

/**
 * Schema mapping with exact filenames as specified
 */
const schemas = {
  'menu.export.req.json': MenuExportReq,
  'menu.export.res.json': MenuExportRes,
  'order.accept.req.json': OrderAcceptReq,
  'order.accept.res.json': OrderAcceptRes,
  'order.validate.req.json': OrderValidateReq,
  'order.validate.res.json': OrderValidateRes
}

console.log('🔨 Building schemas from v1.ts...')
console.log(`📁 Output directory: ${outputDir}`)

// Compile and write each schema
let successCount = 0
Object.entries(schemas).forEach(([filename, schema]) => {
  try {
    const jsonSchema = JSON.stringify(schema, null, 2)
    const outputPath = join(outputDir, filename)
    
    writeFileSync(outputPath, jsonSchema, 'utf8')
    console.log(`✅ Generated ${filename}`)
    successCount++
  } catch (error) {
    console.error(`❌ Failed to generate ${filename}:`, error)
  }
})

console.log(`\n🎉 Schema compilation complete!`)
console.log(`📊 Generated ${successCount}/6 schema files`)

if (successCount === 6) {
  console.log(`📋 All files generated successfully:`)
  Object.keys(schemas).sort().forEach(filename => {
    console.log(`   - ${filename}`)
  })
} else {
  console.error(`⚠️  Expected 6 files but generated ${successCount}`)
  process.exit(1)
}