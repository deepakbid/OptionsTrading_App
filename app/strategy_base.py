"""
Enhanced Strategy Base Class
Provides connection-aware functionality and integrates with the connection manager.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from .connection_manager import connection_manager

logger = logging.getLogger(__name__)

class Strategy(ABC):
    """
    Enhanced Strategy base class with connection management.
    
    All strategies should inherit from this class to get:
    - Connection management
    - Health monitoring
    - Automatic reconnection
    - Connection status awareness
    """
    
    name: str = "Unnamed Strategy"
    required_connection_type: str = "paper"  # "paper" or "real"
    connection_timeout: int = 30  # seconds to wait for connection
    
    def __init__(self):
        self.connection_status = "disconnected"
        self.last_connection_check = None
        self.connection_check_interval = 60  # seconds
        self._connection_callback_registered = False
    
    async def ensure_connection(self) -> bool:
        """
        Ensure we have a healthy connection before trading.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            # Check if we need to verify connection
            if (self.last_connection_check and 
                (datetime.now() - self.last_connection_check).seconds < self.connection_check_interval):
                return connection_manager.is_connected(self.required_connection_type)
            
            # Try to get or establish connection
            success = await connection_manager.ensure_connection(self.required_connection_type)
            
            if success:
                self.connection_status = "connected"
                self.last_connection_check = datetime.now()
                logger.info(f"Strategy {self.name}: Connection established ({self.required_connection_type})")
                return True
            else:
                # Try alternative connection type if available
                alternative_type = "real" if self.required_connection_type == "paper" else "paper"
                if await connection_manager.ensure_connection(alternative_type):
                    self.connection_status = "connected"
                    self.last_connection_check = datetime.now()
                    logger.info(f"Strategy {self.name}: Using alternative connection ({alternative_type})")
                    return True
                
                self.connection_status = "disconnected"
                logger.error(f"Strategy {self.name}: Failed to establish connection")
                return False
                
        except Exception as e:
            logger.error(f"Strategy {self.name}: Connection error: {e}")
            self.connection_status = "error"
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "strategy_name": self.name,
            "required_type": self.required_connection_type,
            "current_status": self.connection_status,
            "last_check": self.last_connection_check.isoformat() if self.last_connection_check else None,
            "connection_manager_status": connection_manager.get_connection_summary()
        }
    
    async def wait_for_connection(self, timeout: int = None) -> bool:
        """
        Wait for connection to be established.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if connection established, False if timeout
        """
        if timeout is None:
            timeout = self.connection_timeout
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            if await self.ensure_connection():
                return True
            
            await asyncio.sleep(2)  # Wait 2 seconds before retry
        
        logger.error(f"Strategy {self.name}: Connection timeout after {timeout} seconds")
        return False
    
    def register_connection_callback(self):
        """Register for connection status change notifications."""
        if not self._connection_callback_registered:
            connection_manager.register_connection_callback(self._on_connection_change)
            self._connection_callback_registered = True
    
    def _on_connection_change(self, connection_type: str, connection_info):
        """Handle connection status changes."""
        if connection_type == self.required_connection_type:
            logger.info(f"Strategy {self.name}: Connection status changed to {connection_info.status.value}")
            
            if connection_info.status.value == "connected":
                self.connection_status = "connected"
            elif connection_info.status.value in ["disconnected", "error"]:
                self.connection_status = "disconnected"
    
    @abstractmethod
    async def run(self, ib, params: dict, log):
        """
        Main strategy execution method.
        
        Args:
            ib: IB connection instance (may be None if using connection manager)
            params: Strategy parameters
            log: Logging function
        """
        pass
    
    async def run_with_connection_management(self, ib, params: dict, log):
        """
        Enhanced run method with connection management.
        Use this instead of the basic run() method for better connection handling.
        
        Args:
            ib: IB connection instance (may be None)
            params: Strategy parameters
            log: Logging function
        """
        try:
            # Ensure we have a connection
            if not await self.ensure_connection():
                log(f"Strategy {self.name}: Failed to establish connection")
                return False
            
            # Register for connection updates
            self.register_connection_callback()
            
            # Run the strategy
            log(f"Strategy {self.name}: Starting with connection status: {self.connection_status}")
            result = await self.run(ib, params, log)
            
            log(f"Strategy {self.name}: Completed with result: {result}")
            return result
            
        except Exception as e:
            log(f"Strategy {self.name}: Error during execution: {e}")
            logger.error(f"Strategy {self.name} execution error: {e}", exc_info=True)
            return False
    
    def is_connection_healthy(self) -> bool:
        """Check if current connection is healthy."""
        return connection_manager.is_connected(self.required_connection_type)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the strategy."""
        health_info = {
            "strategy_name": self.name,
            "connection_status": self.connection_status,
            "connection_healthy": self.is_connection_healthy(),
            "last_connection_check": self.last_connection_check.isoformat() if self.last_connection_check else None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Perform connection check if needed
        if await self.ensure_connection():
            health_info["connection_check_result"] = "success"
        else:
            health_info["connection_check_result"] = "failed"
        
        return health_info
