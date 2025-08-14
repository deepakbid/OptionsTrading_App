#!/usr/bin/env python3
"""
Final test script for connecting to IBKR live trading account
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
        
        try:
            # Use a different client ID for live trading
            ib.connect('127.0.0.1', port=7496, clientId=1201, timeout=10)
            
            # Wait a bit for connection
            time.sleep(2)
            
            if ib.isConnected():
                print(f"✅ SUCCESS: Connected to TWS LIVE on port 7496!")
                
                # Try to get managed accounts - FINAL FIXED VERSION
                try:
                    # Call the managedAccounts method
                    accounts_str = ib.managedAccounts()
                    print(f"Managed accounts type: {type(accounts_str)}")
                    print(f"Managed accounts value: {accounts_str}")
                    
                    if accounts_str and isinstance(accounts_str, str) and accounts_str.strip():
                        print("🎯 LIVE ACCOUNTS FOUND!")
                        accounts_list = [acc.strip() for acc in accounts_str.split(',') if acc.strip()]
                        for acc in accounts_list:
                            print(f"   - {acc}")
                        print(f"Total accounts: {len(accounts_list)}")
                    else:
                        print("⚠️  No live accounts found or accounts string is empty")
                        
                except Exception as e:
                    print(f"Could not get managed accounts: {e}")
                    print(f"Error type: {type(e).__name__}")
                
                # Disconnect
                ib.disconnect()
                print("Disconnected from TWS LIVE")
                return True
            else:
                print(f"❌ FAILED: Not connected after connect call")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Try to disconnect if connected
            try:
                if ib.isConnected():
                    ib.disconnect()
            except:
                pass
        
        print("\n❌ LIVE connection failed!")
        return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_live_connection()
