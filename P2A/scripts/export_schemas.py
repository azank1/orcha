#!/usr/bin/env python3
"""
Export schemas from Engine TypeBox schemas to Python-compatible format.
This script reads the compiled JSON schemas and creates Python dataclass/Pydantic models.
Usage: python scripts/export_schemas.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Path to the compiled schemas from Engine
ENGINE_SCHEMAS_PATH = Path(__file__).parent.parent.parent / "engine" / "schemas" / "json"
OUTPUT_PATH = Path(__file__).parent.parent / "models" / "schemas"
MANIFEST_PATH = Path(__file__).parent.parent / "models" / "schemas_manifest.json"

def json_schema_to_python_type(schema: Dict[str, Any], name: str = "") -> str:
    """Convert JSON schema type to Python type hint."""
    schema_type = schema.get("type", "object")
    
    if schema_type == "string":
        if schema.get("minLength") or schema.get("maxLength"):
            return "str"
        return "str"
    elif schema_type == "integer":
        return "int"
    elif schema_type == "number":
        return "float"
    elif schema_type == "boolean":
        return "bool"
    elif schema_type == "array":
        items = schema.get("items", {})
        item_type = json_schema_to_python_type(items)
        return f"List[{item_type}]"
    elif schema_type == "object":
        return "Dict[str, Any]"  # Simplified for now
    else:
        return "Any"

def generate_pydantic_model(schema: Dict[str, Any], class_name: str) -> str:
    """Generate a Pydantic model from JSON schema."""
    imports = [
        "from typing import Dict, List, Optional, Any, Union",
        "from pydantic import BaseModel, Field"
    ]
    
    class_def = f"class {class_name}(BaseModel):"
    fields = []
    
    # Handle allOf schemas (intersections)
    if "allOf" in schema:
        for sub_schema in schema["allOf"]:
            if "properties" in sub_schema:
                for prop_name, prop_schema in sub_schema["properties"].items():
                    python_type = json_schema_to_python_type(prop_schema, prop_name)
                    
                    # Check if field is required
                    required = prop_name in sub_schema.get("required", [])
                    if not required:
                        python_type = f"Optional[{python_type}]"
                        fields.append(f"    {prop_name}: {python_type} = None")
                    else:
                        fields.append(f"    {prop_name}: {python_type}")
    
    # Handle direct properties
    elif "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            python_type = json_schema_to_python_type(prop_schema, prop_name)
            
            # Check if field is required
            required = prop_name in schema.get("required", [])
            if not required:
                python_type = f"Optional[{python_type}]"
                fields.append(f"    {prop_name}: {python_type} = None")
            else:
                fields.append(f"    {prop_name}: {python_type}")
    
    if not fields:
        fields.append("    pass")
    
    return "\n".join(imports) + "\n\n" + class_def + "\n" + "\n".join(fields)

def export_schemas():
    """Export all schemas from Engine to Python models."""
    
    if not ENGINE_SCHEMAS_PATH.exists():
        print(f"❌ Schema path not found: {ENGINE_SCHEMAS_PATH}")
        print("Please run 'npm run build:schemas' in the Engine directory first.")
        sys.exit(1)
    
    # Ensure output directory exists
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    # Schema file mapping (matches engine/schemas/json filenames)
    schema_files = {
        "menu.export.req.json": "MenuExportRequest",
        "menu.export.res.json": "MenuExportResponse",
        "order.validate.req.json": "OrderValidateRequest",
        "order.validate.res.json": "OrderValidateResponse",
        "order.accept.req.json": "OrderAcceptRequest",
        "order.accept.res.json": "OrderAcceptResponse"
    }
    
    generated_models = []
    
    print("🔄 Exporting schemas from Engine to Python...")
    
    # For manifest: collect sha256 of source files and generated targets
    import hashlib
    manifest_entries = []

    for filename, class_name in schema_files.items():
        schema_path = ENGINE_SCHEMAS_PATH / filename
        
        if not schema_path.exists():
            print(f"⚠️  Schema file not found: {filename}")
            continue
        
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Hash the engine schema for manifest
            with open(schema_path, 'rb') as frb:
                src_bytes = frb.read()
                src_sha = hashlib.sha256(src_bytes).hexdigest()

            # Generate Pydantic model
            model_code = generate_pydantic_model(schema, class_name)
            
            # Write to individual file
            base_name = filename.replace('.json', '').replace('-', '_').replace('.', '_')
            module_name = base_name
            safe_name = f"{base_name}.py"
            output_file = OUTPUT_PATH / safe_name
            with open(output_file, 'w') as f:
                f.write(f'"""{class_name} model generated from TypeBox schema."""\n\n')
                f.write(model_code)
                f.write("\n")
            
            generated_models.append((class_name, module_name))
            manifest_entries.append({
                "source": filename,
                "source_sha256": src_sha,
                "generated": safe_name,
                "class": class_name
            })
            print(f"✓ Generated {class_name} -> {output_file.name}")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
    
    # Generate __init__.py with all exports
    init_content = ['"""Schema models generated from Engine TypeBox schemas."""\n']
    init_content.extend([f"from .{module} import {cls}" for (cls, module) in generated_models])
    init_content.append("\n__all__ = [")
    init_content.extend([f'    "{cls}",' for (cls, _) in generated_models])
    init_content.append("]")
    
    with open(OUTPUT_PATH / "__init__.py", 'w') as f:
        f.write("\n".join(init_content))
    
    # Write manifest file for hash-checking
    with open(MANIFEST_PATH, 'w') as mf:
        json.dump({
            "engine_schemas_dir": str(ENGINE_SCHEMAS_PATH),
            "generated_dir": str(OUTPUT_PATH),
            "entries": manifest_entries
        }, mf, indent=2)

    print(f"\\n🎉 Successfully exported {len(generated_models)} schemas to {OUTPUT_PATH}")
    print("📋 Generated models:")
    for model_name, _ in generated_models:
        print(f"   - {model_name}")

if __name__ == "__main__":
    export_schemas()