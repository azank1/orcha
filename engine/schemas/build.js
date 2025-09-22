#!/usr/bin/env node
/**
 * Build script to compile TypeBox schemas to plain JSON files
 * Usage: npm run build:schemas
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Import schemas from the compiled TypeScript output
import('../dist/schemas/index.js').then(async (schemas) => {
  const {
    MenuExportReq,
    MenuExportRes,
    OrderValidateReq,
    OrderValidateRes,
    OrderAcceptReq,
    OrderAcceptRes
  } = schemas;

  const outputDir = join(__dirname, 'json');

  // Ensure output directory exists
  mkdirSync(outputDir, { recursive: true });

  // Schema definitions to export
  const schemaMap = {
    'menu-export-req.json': MenuExportReq,
    'menu-export-res.json': MenuExportRes,
    'order-validate-req.json': OrderValidateReq,
    'order-validate-res.json': OrderValidateRes,
    'order-accept-req.json': OrderAcceptReq,
    'order-accept-res.json': OrderAcceptRes
  };

  // Compile and write each schema
  Object.entries(schemaMap).forEach(([filename, schema]) => {
    const jsonSchema = JSON.stringify(schema, null, 2);
    const outputPath = join(outputDir, filename);
    
    writeFileSync(outputPath, jsonSchema, 'utf8');
    console.log(`✓ Generated ${filename}`);
  });

  console.log(`\n🎉 All schemas compiled to ${outputDir}`);
  console.log('📋 Schema files:');
  Object.keys(schemaMap).forEach(filename => {
    console.log(`   - ${filename}`);
  });
}).catch(err => {
  console.error('Error importing schemas:', err);
  process.exit(1);
});