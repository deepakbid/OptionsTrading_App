#!/usr/bin/env python3
"""
Detailed test script to check IBKR connection with better error handling
"""
from ib_async import IB
import time

def test_connection():
    print("Testing IBKR connection...")
    
    try:
        # Create IB instance
        ib = IB()
        print(f"IB instance created: {ib}")
        
        # Try to connect with longer timeout
        print("Attempting to connect to TWS on port 7497...")
        print("Make sure TWS is running and API is enabled!")
        
        # Try different ports
        ports_to_try = [7497, 4001, 4002]
        
        for port in ports_to_try:
            print(f"\n--- Trying port {port} ---")
            try:
                ib.connect('127.0.0.1', port, clientId=999, timeout=10)
                
                # Wait a bit for connection
                time.sleep(2)
                
                if ib.isConnected():
                    print(f"✅ SUCCESS: Connected to TWS on port {port}!")
                    
                    # Try to get managed accounts
                    try:
                        accounts = ib.managedAccounts
                        print(f"Managed accounts: {accounts}")
                    except Exception as e:
                        print(f"Could not get managed accounts: {e}")
                    
                    # Disconnect
                    ib.disconnect()
                    print("Disconnected from TWS")
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
        
        print("\n❌ All connection attempts failed!")
        return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_connection()
