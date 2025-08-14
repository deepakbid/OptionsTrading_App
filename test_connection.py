#!/usr/bin/env python3
"""
Quick test script to check IBKR connection
"""
import asyncio
from ib_async import IB

async def test_connection():
    print("Testing IBKR connection...")
    
    try:
        # Create IB instance
        ib = IB()
        print(f"IB instance created: {ib}")
        
        # Try to connect
        print("Attempting to connect to TWS...")
        await ib.connect('127.0.0.1', 7497, clientId=999)
        
        # Check if connected
        if ib.isConnected():
            print("✅ SUCCESS: Connected to TWS!")
            
            # Try to get managed accounts
            try:
                accounts = ib.managedAccounts
                print(f"Managed accounts: {accounts}")
            except Exception as e:
                print(f"Could not get managed accounts: {e}")
            
            # Disconnect
            await ib.disconnect()
            print("Disconnected from TWS")
        else:
            print("❌ FAILED: Not connected after connect call")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_connection())
