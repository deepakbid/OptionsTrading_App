from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(tags=["accounts"])

# Request model for connect endpoint
class ConnectRequest(BaseModel):
    paper_trading: bool = True

@router.get("/")
async def get_accounts():
    """Get all available accounts from TWS IBKR for both paper and live trading."""
    try:
        # Get the singleton IBManager instance
        from app.ib_adapter import IBManager
        ib_manager = IBManager.instance()
        
        # Check if connected (thread-safe)
        is_connected = await ib_manager.is_connected()
        
        if not is_connected:
            # If not connected, return empty list
            return {
                "success": True,
                "accounts": [],
                "paper_count": 0,
                "live_count": 0,
                "message": "Not connected to IBKR. Please connect first."
            }
        
        # Get connection info (thread-safe)
        connection_info = await ib_manager.get_connection_info()
        connection_type = connection_info.get('type')
        
        print(f"DEBUG: Connection info: {connection_info}")
        print(f"DEBUG: Connection type: {connection_type}")
        
        # Get accounts based on connection type
        try:
            if connection_type == 'paper':
                # For paper trading, fetch actual accounts from IBKR
                print(f"DEBUG: Fetching paper trading accounts from IBKR...")
                
                paper_accounts = await ib_manager.get_accounts(paper_trading=True)
                print(f"DEBUG: Fetched paper accounts from IBKR: {paper_accounts}")
                
                formatted_accounts = []
                for account_id in paper_accounts:
                    formatted_accounts.append({
                        "id": account_id,
                        "name": f"{account_id} (Paper)",
                        "type": "paper",
                        "selected": False
                    })
                
                return {
                    "success": True,
                    "accounts": formatted_accounts,
                    "paper_count": len(formatted_accounts),
                    "live_count": 0,
                    "connection_type": "paper",
                    "port": connection_info.get('port', 'unknown')
                }
                
            elif connection_type == 'real':
                # For live trading, fetch actual accounts from IBKR
                print(f"DEBUG: Fetching live trading accounts from IBKR...")
                
                live_accounts = await ib_manager.get_accounts(paper_trading=False)
                print(f"DEBUG: Fetched live accounts from IBKR: {live_accounts}")
                
                formatted_accounts = []
                for account_id in live_accounts:
                    formatted_accounts.append({
                        "id": account_id,
                        "name": f"{account_id} (Live)",
                        "type": "live",
                        "selected": False
                    })
                
                return {
                    "success": True,
                    "accounts": formatted_accounts,
                    "paper_count": 0,
                    "live_count": len(formatted_accounts),
                    "connection_type": "real",
                    "port": connection_info.get('port', 'unknown')
                }
                
            else:
                print(f"DEBUG: Unknown connection type: {connection_type}")
                return {
                    "success": True,
                    "accounts": [],
                    "paper_count": 0,
                    "live_count": 0,
                    "message": f"Unknown connection type: {connection_type}"
                }
                
        except Exception as e:
            print(f"Error getting accounts from IBKR: {e}")
            # Return partial success with error message
            return {
                "success": True,
                "accounts": [],
                "paper_count": 0,
                "live_count": 0,
                "connection_type": connection_type,
                "port": connection_info.get('port', 'unknown'),
                "message": f"Connected to {connection_type} trading but could not fetch accounts: {str(e)}"
            }
        
    except Exception as e:
        print(f"Error in get_accounts endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")

@router.get("/all")
async def get_all_accounts():
    """Get accounts for both paper and live trading environments."""
    try:
        # Get the singleton IBManager instance
        from app.ib_adapter import IBManager
        ib_manager = IBManager.instance()
        
        # This will try to connect to both paper and live to get all accounts
        all_accounts = await ib_manager.get_all_accounts()
        
        # Format the response
        formatted_accounts = []
        
        # Add paper accounts
        for account_id in all_accounts.get("paper", []):
            formatted_accounts.append({
                "id": account_id,
                "name": f"{account_id} (Paper)",
                "type": "paper",
                "selected": False
            })
        
        # Add live accounts
        for account_id in all_accounts.get("real", []):
            formatted_accounts.append({
                "id": account_id,
                "name": f"{account_id} (Live)",
                "type": "live",
                "selected": False
            })
        
        return {
            "success": True,
            "accounts": formatted_accounts,
            "paper_count": len(all_accounts.get("paper", [])),
            "live_count": len(all_accounts.get("real", [])),
            "total_count": len(formatted_accounts)
        }
        
    except Exception as e:
        print(f"Error in get_all_accounts endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch all accounts: {str(e)}")

@router.post("/connect")
async def connect_to_ibkr(
    paper_trading: Optional[bool] = Body(None),
    request: Optional[ConnectRequest] = Body(None)
):
    """
    Connect to TWS IBKR.
    Accepts either:
    1. JSON body with paper_trading field: {"paper_trading": true/false}
    2. ConnectRequest model: {"paper_trading": true/false}
    3. Direct boolean in body (for backward compatibility)
    """
    try:
        # Determine paper_trading value from various sources
        if request is not None:
            paper_trading_value = request.paper_trading
        elif paper_trading is not None:
            paper_trading_value = paper_trading
        else:
            # Default to paper trading if nothing specified
            paper_trading_value = True
        
        # Debug logging
        print("=" * 60)
        print(f"DEBUG: /connect endpoint called")
        print(f"  paper_trading parameter received: {paper_trading_value}")
        print(f"  Type of paper_trading: {type(paper_trading_value)}")
        
        # Ensure it's a boolean
        if isinstance(paper_trading_value, str):
            paper_trading_value = paper_trading_value.lower() in ['true', '1', 'yes', 'paper']
        elif isinstance(paper_trading_value, int):
            paper_trading_value = bool(paper_trading_value)
        
        print(f"  Normalized paper_trading: {paper_trading_value} (type: {type(paper_trading_value)})")
        print("=" * 60)
        
        # Get the singleton IBManager instance
        from app.ib_adapter import IBManager
        ib_manager = IBManager.instance()
        
        # Connect using the IBManager with the correct parameter
        await ib_manager.connect(paper_trading=paper_trading_value)
        
        # Get connection info (thread-safe)
        connection_info = await ib_manager.get_connection_info()
        connection_type = connection_info.get('type')
        
        print(f"DEBUG: After connection, connection_info={connection_info}")
        print(f"DEBUG: Actual connection_type from IBManager: {connection_type}")
        
        # Verify connection type matches request
        expected_type = 'paper' if paper_trading_value else 'real'
        if connection_type != expected_type:
            print(f"WARNING: Connection type mismatch! Expected: {expected_type}, Got: {connection_type}")
        
        print(f"DEBUG: Successfully connected to IBKR {connection_type.upper()} trading")
        
        return {
            "success": True,
            "connected": True,
            "connection_type": connection_type,
            "port": connection_info.get('port'),
            "host": connection_info.get('host'),
            "message": f"Successfully connected to IBKR {connection_type.title()} Trading."
        }
        
    except ConnectionError as e:
        print(f"DEBUG: Connection failed: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "message": f"Failed to connect to IBKR: {str(e)}"
        }
    except Exception as e:
        print(f"DEBUG: Unexpected error in connect_to_ibkr: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "message": f"Unexpected error connecting to IBKR: {str(e)}"
        }

@router.post("/disconnect")
async def disconnect_from_ibkr():
    """Disconnect from TWS IBKR."""
    try:
        # Get the singleton IBManager instance
        from app.ib_adapter import IBManager
        ib_manager = IBManager.instance()
        
        # Check if connected before disconnecting
        was_connected = await ib_manager.is_connected()
        
        if not was_connected:
            return {
                "success": True,
                "connected": False,
                "message": "Already disconnected from IBKR"
            }
        
        # Get connection info before disconnecting
        connection_info = await ib_manager.get_connection_info()
        connection_type = connection_info.get('type', 'unknown')
        
        # Disconnect using the IBManager
        await ib_manager.disconnect()
        
        return {
            "success": True,
            "connected": False,
            "message": f"Successfully disconnected from IBKR {connection_type.title()} Trading"
        }
        
    except Exception as e:
        print(f"Error in disconnect_from_ibkr: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to disconnect from IBKR: {str(e)}"
        }

@router.get("/status")
async def get_connection_status():
    """Get current connection status."""
    try:
        # Get the singleton IBManager instance
        from app.ib_adapter import IBManager
        ib_manager = IBManager.instance()
        
        # Get connection status (thread-safe)
        is_connected = await ib_manager.is_connected()
        
        if not is_connected:
            return {
                "success": True,
                "connected": False,
                "connection_type": None,
                "message": "Not connected to IBKR"
            }
        
        # Get detailed connection info
        connection_info = await ib_manager.get_connection_info()
        
        return {
            "success": True,
            "connected": True,
            "connection_type": connection_info.get('type'),
            "port": connection_info.get('port'),
            "host": connection_info.get('host'),
            "message": f"Connected to IBKR {connection_info.get('type', 'unknown').title()} Trading"
        }
        
    except Exception as e:
        print(f"Error in get_connection_status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection status: {str(e)}")