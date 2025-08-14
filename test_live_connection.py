#!/usr/bin/env python3
"""
Test script for connecting to IBKR live trading account
"""
from ib_async import IB
import time

def test_live_connection():
    print("Testing IBKR LIVE ACCOUNT connection...")
    print("⚠️  WARNING: This will attempt to connect to LIVE trading!")
    
    try:
        # Create IB instance
        ib = IB()
        print(f"IB instance created: {ib}")
        
        # Try to connect to live trading (port 7496)
        print("Attempting to connect to TWS LIVE TRADING on port 7496...")
        print("Make sure TWS is running and LIVE API is enabled!")
        
        # Live trading ports to try
        live_ports = [7496, 4000, 4001]
        
        for port in live_ports:
            print(f"\n--- Trying LIVE port {port} ---")
            try:
                # Use a different client ID for live trading
                ib.connect('127.0.0.1', port, clientId=1201, timeout=10)
                
                # Wait a bit for connection
                time.sleep(2)
                
                if ib.isConnected():
                    print(f"✅ SUCCESS: Connected to TWS LIVE on port {port}!")
                    
                    # Try to get managed accounts
                    try:
                        accounts = ib.managedAccounts
                        print(f"LIVE Managed accounts: {accounts}")
                        
                        if accounts:
                            print("🎯 LIVE ACCOUNTS FOUND!")
                            for acc in accounts.split(','):
                                if acc.strip():
                                    print(f"   - {acc.strip()}")
                        else:
                            print("⚠️  No live accounts found")
                            
                    except Exception as e:
                        print(f"Could not get managed accounts: {e}")
                    
                    # Disconnect
                    ib.disconnect()
                    print("Disconnected from TWS LIVE")
                    return True
                else:
                    print(f"❌ FAILED: Not connected after connect call on port {port}")
                    
            except Exception as e:
                print(f"❌ ERROR on port {port}: {e}")
                print(f"Error type: {type(e).__name__}")
                
                # Try to disconnect if connected
                try:
                    if ib.isConnected():
                        ib.disconnect()
                except:
                    pass
        
        print("\n❌ All LIVE connection attempts failed!")
        print("Make sure:")
        print("1. TWS is running")
        print("2. API is enabled in TWS (File > Global Configuration > API > Settings)")
        print("3. Live trading is enabled (not just paper)")
        print("4. Port 7496 is open for live trading")
        return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_live_connection()
