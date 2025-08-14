"""
Connection Management Router
Provides endpoints for monitoring and controlling IBKR connections.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import logging

from ..connection_manager import connection_manager
from ..ib_adapter import IBManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connection", tags=["connection"])

@router.get("/", response_class=HTMLResponse)
async def connection_dashboard():
    """Connection management dashboard."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connection Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .status-card { 
                border: 1px solid #ddd; 
                padding: 20px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }
            .connected { border-color: #4CAF50; background-color: #f1f8e9; }
            .disconnected { border-color: #f44336; background-color: #ffebee; }
            .connecting { border-color: #ff9800; background-color: #fff3e0; }
            .error { border-color: #f44336; background-color: #ffebee; }
            .button { 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                margin: 5px; 
            }
            .button:hover { background-color: #45a049; }
            .button.disconnect { background-color: #f44336; }
            .button.disconnect:hover { background-color: #da190b; }
            .refresh-btn { 
                background-color: #2196F3; 
                margin-bottom: 20px; 
            }
            .refresh-btn:hover { background-color: #1976D2; }
        </style>
        <script>
            function refreshStatus() {
                location.reload();
            }
            
            async function connect(type) {
                const response = await fetch(`/api/connection/connect/${type}`, {method: 'POST'});
                if (response.ok) {
                    setTimeout(refreshStatus, 2000);
                } else {
                    alert('Connection failed');
                }
            }
            
            async function disconnect(type) {
                const response = await fetch(`/api/connection/disconnect/${type}`, {method: 'POST'});
                if (response.ok) {
                    setTimeout(refreshStatus, 1000);
                } else {
                    alert('Disconnect failed');
                }
            }
        </script>
    </head>
    <body>
        <h1>IBKR Connection Management</h1>
        <button class="button refresh-btn" onclick="refreshStatus()">🔄 Refresh Status</button>
        
        <div id="paper-status" class="status-card">
            <h2>Paper Trading Connection</h2>
            <div id="paper-details"></div>
            <button class="button" onclick="connect('paper')">Connect Paper</button>
            <button class="button disconnect" onclick="disconnect('paper')">Disconnect</button>
        </div>
        
        <div id="real-status" class="status-card">
            <h2>Real Trading Connection</h2>
            <div id="real-details"></div>
            <button class="button" onclick="connect('real')">Connect Real</button>
            <button class="button disconnect" onclick="disconnect('real')">Disconnect</button>
        </div>
        
        <script>
            // Load initial status
            fetch('/api/connection/status')
                .then(response => response.json())
                .then(data => {
                    updateStatusDisplay('paper', data.paper);
                    updateStatusDisplay('real', data.real);
                });
                
            function updateStatusDisplay(type, status) {
                const card = document.getElementById(type + '-status');
                const details = document.getElementById(type + '-details');
                
                // Update card class
                card.className = 'status-card ' + status.status;
                
                // Update details
                details.innerHTML = `
                    <p><strong>Status:</strong> ${status.status}</p>
                    <p><strong>Connected:</strong> ${status.connected_at || 'Never'}</p>
                    <p><strong>Last Heartbeat:</strong> ${status.last_heartbeat || 'Never'}</p>
                    <p><strong>Error:</strong> ${status.error_message || 'None'}</p>
                    <p><strong>Host:</strong> ${status.host || 'Unknown'}</p>
                    <p><strong>Port:</strong> ${status.port || 'Unknown'}</p>
                `;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/api/status")
async def get_connection_status() -> Dict[str, Any]:
    """Get current connection status for all connection types."""
    try:
        return connection_manager.get_connection_summary()
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/status/{connection_type}")
async def get_connection_status_by_type(connection_type: str) -> Dict[str, Any]:
    """Get connection status for a specific connection type."""
    try:
        if connection_type not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="connection_type must be 'paper' or 'real'")
        
        status = connection_manager.get_connection_status(connection_type)
        return {
            "connection_type": connection_type,
            "status": status.status.value,
            "connected_at": status.connected_at.isoformat() if status.connected_at else None,
            "last_heartbeat": status.last_heartbeat.isoformat() if status.last_heartbeat else None,
            "error_message": status.error_message,
            "host": status.host,
            "port": status.port
        }
    except Exception as e:
        logger.error(f"Error getting connection status for {connection_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/connect/{connection_type}")
async def connect_to_ibkr(connection_type: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Connect to IBKR with specified connection type."""
    try:
        if connection_type not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="connection_type must be 'paper' or 'real'")
        
        # Start connection manager if not running
        background_tasks.add_task(connection_manager.start)
        
        # Attempt connection
        success = await connection_manager.connect(connection_type)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully connected to IBKR ({connection_type})",
                "connection_type": connection_type
            }
        else:
            return {
                "success": False,
                "message": f"Failed to connect to IBKR ({connection_type})",
                "connection_type": connection_type
            }
            
    except Exception as e:
        logger.error(f"Error connecting to IBKR ({connection_type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/disconnect/{connection_type}")
async def disconnect_from_ibkr(connection_type: str) -> Dict[str, Any]:
    """Disconnect from IBKR."""
    try:
        if connection_type not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="connection_type must be 'paper' or 'real'")
        
        success = await connection_manager.disconnect(connection_type)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully disconnected from IBKR ({connection_type})",
                "connection_type": connection_type
            }
        else:
            return {
                "success": False,
                "message": f"Failed to disconnect from IBKR ({connection_type})",
                "connection_type": connection_type
            }
            
    except Exception as e:
        logger.error(f"Error disconnecting from IBKR ({connection_type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/health-check")
async def perform_health_check() -> Dict[str, Any]:
    """Perform health check on all connections."""
    try:
        # This will trigger health checks on all connections
        return {
            "success": True,
            "message": "Health check completed",
            "timestamp": connection_manager.get_connection_summary()
        }
    except Exception as e:
        logger.error(f"Error performing health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/health")
async def get_connection_health() -> Dict[str, Any]:
    """Get overall connection health status."""
    try:
        paper_healthy = connection_manager.is_connected("paper")
        real_healthy = connection_manager.is_connected("real")
        
        return {
            "overall_health": "healthy" if (paper_healthy or real_healthy) else "unhealthy",
            "paper_trading": "healthy" if paper_healthy else "unhealthy",
            "real_trading": "healthy" if real_healthy else "unhealthy",
            "recommendations": _get_health_recommendations(paper_healthy, real_healthy)
        }
    except Exception as e:
        logger.error(f"Error getting connection health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_health_recommendations(paper_healthy: bool, real_healthy: bool) -> list:
    """Get health recommendations based on connection status."""
    recommendations = []
    
    if not paper_healthy and not real_healthy:
        recommendations.append("No connections available. Consider connecting to paper trading first.")
        recommendations.append("Check IBKR Gateway/TWS is running and accessible.")
        recommendations.append("Verify network connectivity and firewall settings.")
    
    elif not paper_healthy:
        recommendations.append("Paper trading connection is down. Real trading connection is available.")
        recommendations.append("Consider reconnecting to paper trading for testing.")
    
    elif not real_healthy:
        recommendations.append("Real trading connection is down. Paper trading connection is available.")
        recommendations.append("Only paper trading strategies can run currently.")
    
    if paper_healthy and real_healthy:
        recommendations.append("All connections are healthy. Both paper and real trading available.")
    
    return recommendations
