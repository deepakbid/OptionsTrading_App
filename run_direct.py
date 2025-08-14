#!/usr/bin/env python3
"""
Direct strategy runner to bypass CLI issues.
"""
import asyncio
import sys
import os

# Add app/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def main():
    try:
        from file_strategy_loader import file_strategy_loader
        from connection_manager import connection_manager
        
        print("🚀 Starting direct strategy runner...")
        
        # Start connection manager
        await connection_manager.start()
        
        # Connect to real trading
        ok = await connection_manager.ensure_connection("real")
        if not ok:
            print("❌ Failed to connect to IBKR")
            return
        
        print("✅ Connected to IBKR")
        
        # Load strategy
        strategy_class = file_strategy_loader.load_strategy_from_file("futures_mnq_strategy.py")
        if not strategy_class:
            print("❌ Failed to load strategy")
            return
        
        print(f"✅ Loaded strategy: {strategy_class.__name__}")
        
        # Create strategy instance
        strategy = strategy_class()
        
        # Set parameters
        strategy.params = {
            'tickers': ['MNQ'],
            'accounts': ['U2211406'],
            'paper_trading': False,
            'strategy_name': 'futures_mnq_strategy',
            'expiry': '202509',
            'limit_offset': 0.25,
            'stop_loss_points': 5.0,
            'take_profit_mult': 2.0,
            'use_delayed': False,
            'tif': 'DAY',
            'limit_timeout': 30,
            'avg_cost_is_price': True
        }
        
        # Set IB connection
        from ib_adapter import IBManager
        strategy.ib = IBManager.instance().ib
        
        print("🎯 Running strategy...")
        print("Press Ctrl+C to stop")
        
        # Run strategy
        await strategy.run(print)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await connection_manager.stop()
        except:
            pass

if __name__ == "__main__":
    # Windows: prefer selector policy
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
