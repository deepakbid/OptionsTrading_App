#!/usr/bin/env python3
"""
Test script for REAL/LIVE accounts only (no paper trading)
"""
from ib_async import IB
import time

def test_real_accounts_only():
    print("Testing IBKR REAL/LIVE ACCOUNTS ONLY...")
    print("⚠️  WARNING: This will connect to LIVE trading only!")
    
    try:
        # Create IB instance
        ib = IB()
        print(f"IB instance created: {ib}")
        
        # Connect to LIVE trading only (port 7496)
        print("Connecting to TWS LIVE TRADING on port 7496...")
        
        try:
            # Use client ID 1201 for live trading
            ib.connect('127.0.0.1', port=7496, clientId=1201, timeout=10)
            
            # Wait for connection
            time.sleep(2)
            
            if ib.isConnected():
                print("✅ SUCCESS: Connected to TWS LIVE on port 7496!")
                
                # Get managed accounts
                try:
                    accounts_list = ib.managedAccounts()
                    print(f"Managed accounts type: {type(accounts_list)}")
                    print(f"Managed accounts value: {accounts_list}")
                    
                    if accounts_list and isinstance(accounts_list, list) and len(accounts_list) > 0:
                        print(f"\n🎯 LIVE ACCOUNTS FOUND: {len(accounts_list)} accounts")
                        print("=" * 50)
                        
                        for i, acc in enumerate(accounts_list, 1):
                            print(f"{i:2d}. {acc}")
                        
                        print("=" * 50)
                        print(f"Total LIVE accounts: {len(accounts_list)}")
                        
                        # Test account details
                        if len(accounts_list) > 0:
                            first_account = accounts_list[0]
                            print(f"\nTesting first account: {first_account}")
                            
                            # Try to get account summary for first account
                            try:
                                print("Requesting account summary...")
                                ib.reqAccountSummary(1, first_account, "TotalCashValue,NetLiquidation")
                                time.sleep(1)
                                
                                if hasattr(ib, 'accountSummary') and ib.accountSummary:
                                    print("Account summary received:")
                                    for summary in ib.accountSummary:
                                        if hasattr(summary, 'account') and summary.account == first_account:
                                            print(f"  Account: {summary.account}")
                                            print(f"  Tag: {getattr(summary, 'tag', 'N/A')}")
                                            print(f"  Value: {getattr(summary, 'value', 'N/A')}")
                                            print(f"  Currency: {getattr(summary, 'currency', 'N/A')}")
                                else:
                                    print("No account summary received")
                                    
                            except Exception as e:
                                print(f"Could not get account summary: {e}")
                        
                    else:
                        print("⚠️  No live accounts found")
                        
                except Exception as e:
                    print(f"Could not get managed accounts: {e}")
                    print(f"Error type: {type(e).__name__}")
                
                # Disconnect
                ib.disconnect()
                print("\nDisconnected from TWS LIVE")
                return True
            else:
                print("❌ FAILED: Not connected after connect call")
                
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
    test_real_accounts_only()
