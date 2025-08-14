#!/usr/bin/env python3
"""
Test script to manually test FastAPI app creation
"""
from fastapi import FastAPI
from app.routers import strategies, accounts

def test_app_creation():
    print("Testing FastAPI app creation...")
    
    try:
        # Create app
        app = FastAPI(title="Test App")
        print("✅ FastAPI app created")
        
        # Include routers
        print("Including strategies router...")
        app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
        print("✅ Strategies router included")
        
        print("Including accounts router...")
        app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
        print("✅ Accounts router included")
        
        # Check routes
        print("\nRegistered routes:")
        for route in app.routes:
            if hasattr(route, 'path'):
                print(f"  {route.path}")
        
        print("\n✅ App creation successful!")
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_app_creation()
