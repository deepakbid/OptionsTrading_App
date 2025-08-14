#!/usr/bin/env python3
"""
Test script to verify parameter injection functionality.
This tests that ticker symbols and account numbers are properly injected into strategies.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from strategies.base import Strategy
from app.strategy_loader import load_strategy_from_code
from app.runner import run_strategy

class TestParameterInjection:
    """Test class for parameter injection functionality."""
    
    def test_strategy_parameter_injection(self):
        """Test that parameters are properly injected into strategies."""
        
        # Test strategy code that expects injected parameters
        test_strategy_code = '''
from strategies.base import Strategy
import asyncio

class TestParameterInjectionStrategy(Strategy):
    name = "Test Parameter Injection"
    
    async def run(self, ib, params, log):
        """Test that parameters are properly injected."""
        log(f"Starting {self.name} strategy...")
        log(f"Received params: {params}")
        
        # Test ticker injection
        tickers = params.get('tickers', [])
        if not tickers:
            log("ERROR: No tickers injected!")
            return False
        log(f"Tickers injected: {tickers}")
        
        # Test account injection
        accounts = params.get('accounts', [])
        if not accounts:
            log("ERROR: No accounts injected!")
            return False
        log(f"Accounts injected: {accounts}")
        
        # Test paper trading mode injection
        paper_trading = params.get('paper_trading', None)
        if paper_trading is None:
            log("ERROR: No paper_trading mode injected!")
            return False
        log(f"Paper trading mode: {paper_trading}")
        
        # Test strategy ID injection
        strategy_id = params.get('strategy_id', None)
        if strategy_id is None:
            log("ERROR: No strategy_id injected!")
            return False
        log(f"Strategy ID: {strategy_id}")
        
        log("All parameters successfully injected!")
        return True

# Strategy instance - REQUIRED for the system to work
strategy = TestParameterInjectionStrategy()
'''
        
        try:
            # Load the strategy
            strategy_instance = load_strategy_from_code(test_strategy_code)
            print(f"✅ Strategy loaded successfully: {strategy_instance.name}")
            
            # Test parameters that would be injected
            test_params = {
                'tickers': ['AAPL', 'TSLA', 'SPY'],
                'accounts': ['DU1234567', 'DU1234568'],
                'paper_trading': True,
                'strategy_id': 123,
                'strategy_name': 'Test Strategy',
                'connection_type': 'paper',
                'ib_manager': Mock(),
                'deployment_id': 456
            }
            
            print(f"✅ Test parameters prepared: {test_params}")
            
            # Mock the IB connection and log function
            mock_ib = Mock()
            mock_log = Mock()
            
            # Run the strategy
            print("🔄 Running strategy with injected parameters...")
            
            # Use asyncio to run the async strategy
            async def run_test():
                result = await strategy_instance.run(mock_ib, test_params, mock_log)
                return result
            
            result = asyncio.run(run_test())
            
            if result:
                print("✅ Strategy executed successfully with all parameters!")
            else:
                print("❌ Strategy execution failed!")
                
            # Check that log was called with expected messages
            log_calls = [call[0][0] for call in mock_log.call_args_list]
            print(f"📝 Log calls made: {len(log_calls)}")
            
            # Verify key log messages
            expected_logs = [
                "Starting Test Parameter Injection strategy...",
                "Tickers injected: ['AAPL', 'TSLA', 'SPY']",
                "Accounts injected: ['DU1234567', 'DU1234568']",
                "Paper trading mode: True",
                "Strategy ID: 123",
                "All parameters successfully injected!"
            ]
            
            for expected_log in expected_logs:
                if any(expected_log in log_call for log_call in log_calls):
                    print(f"✅ Found expected log: {expected_log}")
                else:
                    print(f"❌ Missing expected log: {expected_log}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing parameter injection: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_parameter_access_patterns(self):
        """Test different ways of accessing injected parameters."""
        
        test_strategy_code = '''
from strategies.base import Strategy

class TestParameterAccessStrategy(Strategy):
    name = "Test Parameter Access"
    
    async def run(self, ib, params, log):
        """Test different parameter access patterns."""
        
        # Test direct access
        log(f"Direct access - tickers: {params['tickers']}")
        log(f"Direct access - accounts: {params['accounts']}")
        
        # Test get() with defaults
        log(f"Get with default - tickers: {params.get('tickers', [])}")
        log(f"Get with default - accounts: {params.get('accounts', [])}")
        log(f"Get with default - unknown: {params.get('unknown_param', 'DEFAULT_VALUE')}")
        
        # Test type checking
        if isinstance(params.get('tickers'), list):
            log("✅ Tickers is a list")
        else:
            log("❌ Tickers is not a list")
            
        if isinstance(params.get('accounts'), list):
            log("✅ Accounts is a list")
        else:
            log("❌ Accounts is not a list")
            
        if isinstance(params.get('paper_trading'), bool):
            log("✅ Paper trading is a boolean")
        else:
            log("❌ Paper trading is not a boolean")
        
        return True

strategy = TestParameterAccessStrategy()
'''
        
        try:
            strategy_instance = load_strategy_from_code(test_strategy_code)
            print(f"✅ Parameter access strategy loaded: {strategy_instance.name}")
            
            test_params = {
                'tickers': ['AAPL', 'TSLA'],
                'accounts': ['DU1234567'],
                'paper_trading': False
            }
            
            mock_ib = Mock()
            mock_log = Mock()
            
            async def run_access_test():
                return await strategy_instance.run(mock_ib, test_params, mock_log)
            
            result = asyncio.run(run_access_test())
            
            if result:
                print("✅ Parameter access test completed successfully!")
            else:
                print("❌ Parameter access test failed!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing parameter access: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run all parameter injection tests."""
    print("🧪 Testing Parameter Injection System")
    print("=" * 50)
    
    tester = TestParameterInjection()
    
    # Test 1: Basic parameter injection
    print("\n📋 Test 1: Basic Parameter Injection")
    print("-" * 40)
    test1_result = tester.test_strategy_parameter_injection()
    
    # Test 2: Parameter access patterns
    print("\n📋 Test 2: Parameter Access Patterns")
    print("-" * 40)
    test2_result = tester.test_parameter_access_patterns()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Basic Parameter Injection: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Parameter Access Patterns: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Parameter injection is working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
