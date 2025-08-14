#!/usr/bin/env python3
"""
Test script for Task Manager functionality.
This script tests the parameter injection and Task Manager visibility features.
"""

import asyncio
import sys
import os

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_task_manager_functionality():
    """Test the Task Manager functionality."""
    print("🧪 Testing Task Manager Functionality...")
    
    try:
        # Test 1: Import the runner module
        print("\n1️⃣ Testing module imports...")
        from runner import (
            TaskRegistry, 
            task_registry, 
            get_task_manager_info,
            create_task_manager_description,
            set_process_title
        )
        print("✅ All runner modules imported successfully")
        
        # Test 2: Test TaskRegistry functionality
        print("\n2️⃣ Testing TaskRegistry...")
        registry = TaskRegistry()
        print("✅ TaskRegistry created successfully")
        
        # Test 3: Test task manager description creation
        print("\n3️⃣ Testing task manager description creation...")
        description = create_task_manager_description(
            strategy_name="Test Strategy",
            strategy_id=123,
            tickers=["AAPL", "TSLA"],
            accounts=["DU1234567"],
            paper_trading=True,
            deployment_id=456
        )
        print(f"✅ Task manager description created: {description}")
        
        # Test 4: Test process title setting (this will show in console)
        print("\n4️⃣ Testing process title setting...")
        try:
            set_process_title("Test Strategy Process Title")
            print("✅ Process title set successfully")
        except Exception as e:
            print(f"⚠️ Process title setting failed (expected on some systems): {e}")
        
        # Test 5: Test task manager info retrieval
        print("\n5️⃣ Testing task manager info retrieval...")
        info = get_task_manager_info()
        print(f"✅ Task manager info retrieved: {info}")
        
        # Test 6: Test task registry operations
        print("\n6️⃣ Testing task registry operations...")
        
        # Create a mock task
        mock_task = asyncio.create_task(asyncio.sleep(1))
        mock_task_info = {
            "strategy_id": 999,
            "strategy_name": "Mock Test Strategy",
            "tickers": ["SPY", "QQQ"],
            "accounts": ["DU9999999"],
            "paper_trading": False,
            "deployment_id": 999,
            "start_time": "2024-01-01T00:00:00",
            "process_id": os.getpid(),
            "task_manager_description": "Mock strategy for testing"
        }
        
        # Add task to registry
        await registry.add(999, mock_task, mock_task_info)
        print("✅ Mock task added to registry")
        
        # Check if running
        is_running = registry.is_running(999)
        print(f"✅ Task running status: {is_running}")
        
        # Get task info
        task_info = registry.get_task_info(999)
        print(f"✅ Task info retrieved: {task_info}")
        
        # Get all running tasks
        running_tasks = registry.get_all_running_tasks()
        print(f"✅ All running tasks: {running_tasks}")
        
        # Clean up
        await registry.cleanup(999)
        print("✅ Task cleanup completed")
        
        print("\n🎉 All Task Manager tests passed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_parameter_injection():
    """Test parameter injection functionality."""
    print("\n🧪 Testing Parameter Injection...")
    
    try:
        # Test parameter injection in strategy runner
        from runner import run_strategy
        
        # Mock parameters
        mock_params = {
            "strategy_id": 123,
            "strategy_name": "Test Strategy",
            "tickers": ["AAPL", "TSLA", "SPY"],
            "accounts": ["DU1234567", "DU1234568"],
            "paper_trading": True,
            "deployment_id": 456
        }
        
        print(f"✅ Mock parameters created: {mock_params}")
        
        # Test task manager description creation with these params
        from runner import create_task_manager_description
        description = create_task_manager_description(
            mock_params["strategy_name"],
            mock_params["strategy_id"],
            mock_params["tickers"],
            mock_params["accounts"],
            mock_params["paper_trading"],
            mock_params["deployment_id"]
        )
        
        print(f"✅ Task manager description: {description}")
        
        # Verify the description contains all key information
        assert "Test Strategy" in description
        assert "123" in description
        assert "AAPL" in description
        assert "TSLA" in description
        assert "SPY" in description
        assert "DU1234567" in description
        assert "DU1234568" in description
        assert "📝 Paper" in description
        assert "456" in description
        
        print("✅ All parameter injection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Parameter injection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Task Manager and Parameter Injection Tests...")
    print("=" * 60)
    
    # Test Task Manager functionality
    task_manager_success = await test_task_manager_functionality()
    
    # Test parameter injection
    param_injection_success = await test_parameter_injection()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"Task Manager Functionality: {'✅ PASSED' if task_manager_success else '❌ FAILED'}")
    print(f"Parameter Injection: {'✅ PASSED' if param_injection_success else '❌ FAILED'}")
    
    if task_manager_success and param_injection_success:
        print("\n🎉 All tests passed! Task Manager is working correctly.")
        print("\n💡 To see this in action:")
        print("1. Start the web application: python run.py")
        print("2. Open http://localhost:8000 in your browser")
        print("3. Go to the '🔄 Task Manager' tab")
        print("4. Deploy a strategy to see it appear in the dashboard")
        print("5. Check Windows Task Manager for the descriptive process names")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
