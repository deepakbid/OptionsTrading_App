#!/usr/bin/env python3
"""
Test script for the connection manager.
"""
import sys
import os
import asyncio

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_connection_manager():
    """Test the connection manager functionality."""
    print("Testing Connection Manager...")
    
    try:
        from connection_manager import connection_manager
        
        print("✓ Connection manager imported successfully")
        
        # Test connection status
        print("\n--- Connection Status ---")
        status = connection_manager.get_connection_summary()
        for conn_type, conn_info in status.items():
            print(f"{conn_type.upper()}: {conn_info['status']}")
        
        # Test connection health
        print("\n--- Connection Health ---")
        paper_healthy = connection_manager.is_connected("paper")
        real_healthy = connection_manager.is_connected("real")
        print(f"Paper Trading: {'✓ Healthy' if paper_healthy else '✗ Unhealthy'}")
        print(f"Real Trading: {'✓ Healthy' if real_healthy else '✗ Unhealthy'}")
        
        # Test connection establishment with REAL trading (since TWS real is active)
        print("\n--- Testing REAL Trading Connection ---")
        print("Note: Testing real trading connection since TWS real is active")
        
        try:
            success = await connection_manager.connect("real")
            if success:
                print("✓ Real trading connection established successfully!")
                
                # Test getting accounts
                print("\n--- Testing Account Access ---")
                try:
                    accounts = await connection_manager.ib_manager.get_accounts(paper_trading=False)
                    print(f"✓ Found {len(accounts)} real trading accounts: {accounts}")
                except Exception as e:
                    print(f"✗ Error getting accounts: {e}")
                
                # Test connection info
                print("\n--- Testing Connection Info ---")
                try:
                    conn_info = await connection_manager.ib_manager.get_connection_info()
                    print(f"✓ Connection info: {conn_info}")
                except Exception as e:
                    print(f"✗ Error getting connection info: {e}")
                
                # Disconnect after testing
                print("\n--- Disconnecting ---")
                await connection_manager.disconnect("real")
                print("✓ Disconnected from real trading")
                
            else:
                print("✗ Real trading connection failed")
        except Exception as e:
            print(f"✗ Connection error: {e}")
        
        print("\n✓ Connection manager test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error testing connection manager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection_manager())
