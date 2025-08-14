#!/usr/bin/env python3
"""
Test script to debug the connection logic
"""
import asyncio
import threading

def _connect_sync(host: str, port: int, client_id: int, timeout: int = 10):
    """Synchronous connection helper to avoid event loop conflicts."""
    try:
        from ib_async import IB
        ib = IB()
        print(f"DEBUG: Attempting to connect to {host}:{port} with clientId {client_id}")
        ib.connect(host, port, clientId=client_id, timeout=timeout)
        
        # Wait a bit for connection
        import time
        time.sleep(2)
        
        if ib.isConnected():
            print(f"DEBUG: Successfully connected to {host}:{port}")
            # Get accounts
            accounts = ib.managedAccounts()
            ib.disconnect()
            return True, accounts, None
        else:
            print(f"DEBUG: Connection failed to {host}:{port}")
            ib.disconnect()
            return False, None, "Connection failed"
            
    except Exception as e:
        print(f"DEBUG: Exception connecting to {host}:{port}: {e}")
        return False, None, str(e)

async def test_connection_logic():
    """Test the connection logic."""
    print("Testing connection logic...")
    
    # Test paper trading (should connect to port 7497)
    print("\n=== Testing PAPER trading ===")
    paper_trading = True
    print(f"paper_trading parameter: {paper_trading}")
    
    if paper_trading:
        print("DEBUG: Attempting to connect to PAPER trading (port 7497)...")
        
        # Use threading to avoid event loop conflicts
        def connect_paper():
            return _connect_sync('127.0.0.1', 7497, 1101, 10)
        
        # Run in thread to avoid event loop conflicts
        loop = asyncio.get_event_loop()
        success, accounts, error = await loop.run_in_executor(None, connect_paper)
        
        if success:
            print(f"DEBUG: Paper trading connection successful")
            print(f"Result: Paper trading connected with {len(accounts) if accounts else 0} accounts")
        else:
            print(f"DEBUG: Paper trading connection failed: {error}")
            print(f"Result: Paper trading failed - {error}")
    else:
        print("DEBUG: This should not happen - paper_trading is False")
    
    # Test live trading (should connect to port 7496)
    print("\n=== Testing LIVE trading ===")
    paper_trading = False
    print(f"paper_trading parameter: {paper_trading}")
    
    if not paper_trading:
        print("DEBUG: Attempting to connect to LIVE trading (port 7496)...")
        
        # Use threading to avoid event loop conflicts
        def connect_live():
            return _connect_sync('127.0.0.1', 7496, 1201, 10)
        
        # Run in thread to avoid event loop conflicts
        loop = asyncio.get_event_loop()
        success, accounts, error = await loop.run_in_executor(None, connect_live)
        
        if success:
            print(f"DEBUG: Live trading connection successful")
            print(f"Result: Live trading connected with {len(accounts) if accounts else 0} accounts")
        else:
            print(f"DEBUG: Live trading connection failed: {error}")
            print(f"Result: Live trading failed - {error}")
    else:
        print("DEBUG: This should not happen - paper_trading is True")

if __name__ == "__main__":
    asyncio.run(test_connection_logic())
