#!/usr/bin/env python3
"""
FoodTec Environment Variable Verification Script

Checks that all required FoodTec configuration variables are present in .env
and warns about any missing or empty values.

Usage:
    python verify_foodtec_env.py

Expected .env keys:
- FOODTEC_BASE: Base API URL
- FOODTEC_USER: Username (usually 'apiclient')
- FOODTEC_MENU_PASS: Password for menu endpoints
- FOODTEC_VALIDATE_PASS: Password for order validation
- FOODTEC_ACCEPT_PASS: Password for order submission
- FOODTEC_STORE_ID: Store identifier (e.g., 4203)
- FOODTEC_TIMEOUT: Request timeout in seconds
"""

import os
import sys
from typing import Dict, List, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, reading from environment only")


def check_foodtec_env() -> Tuple[bool, List[str]]:
    """Check all required FoodTec environment variables.
    
    Returns:
        Tuple of (all_present: bool, warnings: List[str])
    """
    required_vars = {
        'FOODTEC_BASE': 'Base API URL',
        'FOODTEC_USER': 'Username (usually apiclient)',
        'FOODTEC_MENU_PASS': 'Password for menu endpoints',
        'FOODTEC_VALIDATE_PASS': 'Password for order validation',
        'FOODTEC_ACCEPT_PASS': 'Password for order submission',
        'FOODTEC_STORE_ID': 'Store identifier (e.g., 4203)',
        'FOODTEC_TIMEOUT': 'Request timeout in seconds'
    }
    
    warnings = []
    missing_vars = []
    
    print("🔍 Checking FoodTec Environment Variables...")
    print("=" * 50)
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        
        if value is None:
            missing_vars.append(var_name)
            print(f"❌ {var_name}: MISSING")
            warnings.append(f"Missing required variable: {var_name} ({description})")
        elif value.strip() == "":
            print(f"⚠️  {var_name}: EMPTY")
            warnings.append(f"Empty variable: {var_name} ({description})")
        else:
            # Mask sensitive values for display
            if 'PASS' in var_name:
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"✅ {var_name}: {display_value}")
    
    print("=" * 50)
    
    if missing_vars:
        print(f"\n💥 {len(missing_vars)} required variables are missing!")
        for var in missing_vars:
            print(f"   • {var}")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings found:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not warnings and not missing_vars:
        print("\n🎉 All FoodTec environment variables are properly configured!")
        
        # Test URL construction
        base_url = os.getenv('FOODTEC_BASE', '').rstrip('/')
        store_id = os.getenv('FOODTEC_STORE_ID')
        if base_url and store_id:
            menu_url = f"{base_url}/store/{store_id}/menu/categories"
            print(f"\n📍 Example menu URL: {menu_url}")
    
    all_present = len(missing_vars) == 0
    return all_present, warnings


def main():
    """Main verification function."""
    print("FoodTec Environment Variable Checker")
    print("====================================\n")
    
    all_present, warnings = check_foodtec_env()
    
    if not all_present:
        print(f"\n❌ Configuration incomplete. Please check your .env file.")
        sys.exit(1)
    elif warnings:
        print(f"\n⚠️  Configuration has warnings but should work.")
        sys.exit(0)
    else:
        print(f"\n✅ Configuration is complete and ready!")
        sys.exit(0)


if __name__ == "__main__":
    main()