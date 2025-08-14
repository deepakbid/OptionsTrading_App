#!/usr/bin/env python3
"""
Test script to verify the setup and imports.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required imports work."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from app.config import IB_HOST, IB_PORT
        print(f"✓ Config loaded: {IB_HOST}:{IB_PORT}")
        
        from app.models import StrategyModel
        print("✓ Models imported")
        
        from strategies.base import Strategy
        print("✓ Strategy base imported")
        
        # Test ib_insync import (this might fail if not installed)
        try:
            from ib_insync import IB
            print("✓ ib_insync imported")
        except ImportError as e:
            print(f"⚠ ib_insync not available: {e}")
            print("  This is expected if ib-api-reloaded is not installed")
        
        print("\n✅ All core imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_strategy_loading():
    """Test strategy loading functionality."""
    try:
        from app.strategy_loader import load_strategy_from_code
        
        # Test strategy code
        test_code = """
from strategies.base import Strategy
import asyncio

class TestStrategy(Strategy):
    name = "Test Strategy"
    
    async def run(self, ib, params, log):
        log("Test strategy running...")
        await asyncio.sleep(0.1)
        log("Test strategy completed!")
"""
        
        strategy = load_strategy_from_code(test_code)
        print(f"✓ Strategy loaded: {strategy.name}")
        return True
        
    except Exception as e:
        print(f"❌ Strategy loading failed: {e}")
        return False

if __name__ == "__main__":
    print("Options Strategy Web App - Setup Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_strategy_loading()
    
    if success:
        print("\n🎉 Setup looks good! You can run the app with:")
        print("  python run.py")
        print("  or")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n❌ Setup issues found. Please check the errors above.")
        sys.exit(1)
