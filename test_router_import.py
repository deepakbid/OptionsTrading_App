#!/usr/bin/env python3
"""
Test script to check router imports
"""
import sys
import traceback

def test_imports():
    print("Testing router imports...")
    
    try:
        print("1. Testing accounts router import...")
        from app.routers.accounts import router
        print("   ✅ Accounts router imported successfully")
        
        print("2. Testing IBManager import...")
        from app.ib_adapter import IBManager
        print("   ✅ IBManager imported successfully")
        
        print("3. Testing router registration...")
        print(f"   Router prefix: {router.prefix}")
        print(f"   Router tags: {router.tags}")
        
        print("4. Testing router endpoints...")
        for route in router.routes:
            print(f"   - {route.methods} {route.path}")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()
