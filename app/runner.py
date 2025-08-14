"""
Async task runner for executing strategies and managing logs.
"""
import asyncio
import json
import time
import os
import sys
import platform
from typing import Dict, List, Optional
from datetime import datetime
from .ib_adapter import IBManager
from .strategy_loader import load_strategy_from_code
from .connection_manager import connection_manager

# Windows-specific imports for task manager visibility
if platform.system() == "Windows":
    try:
        import psutil
        import win32api
        import win32con
        import win32process
        import win32gui
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        print("Windows task manager enhancements not available. Install pywin32 and psutil for full functionality.")
else:
    WINDOWS_AVAILABLE = False

class TaskRegistry:
    def __init__(self):
        self.tasks: Dict[int, asyncio.Task] = {}
        self.logs: Dict[int, List[str]] = {}
        self.task_info: Dict[int, dict] = {}  # Store task metadata
        self._lock = asyncio.Lock()

    async def log(self, sid: int, msg: str):
        """Add a log message for a strategy."""
        async with self._lock:
            if sid not in self.logs:
                self.logs[sid] = []
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logs[sid].append(f"[{timestamp}] {msg}")

    def get_logs(self, sid: int) -> List[str]:
        """Get logs for a strategy."""
        return self.logs.get(sid, [])

    async def add(self, sid: int, task: asyncio.Task, task_info: dict):
        """Add a running task with metadata."""
        async with self._lock:
            self.tasks[sid] = task
            self.task_info[sid] = task_info

    def is_running(self, sid: int) -> bool:
        """Check if a strategy is running."""
        task = self.tasks.get(sid)
        return task is not None and not task.done()

    def get_task_info(self, sid: int) -> Optional[dict]:
        """Get task metadata."""
        return self.task_info.get(sid)

    def get_all_running_tasks(self) -> Dict[int, dict]:
        """Get all running tasks with their metadata."""
        running_tasks = {}
        for sid, task in self.tasks.items():
            if not task.done():
                running_tasks[sid] = self.task_info.get(sid, {})
        return running_tasks

    async def cancel(self, sid: int) -> bool:
        """Cancel a running strategy."""
        async with self._lock:
            task = self.tasks.get(sid)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                await self.log(sid, "Strategy cancelled by user")
                return True
            return False

    async def cleanup(self, sid: int):
        """Clean up completed tasks."""
        async with self._lock:
            task = self.tasks.get(sid)
            if task and task.done():
                del self.tasks[sid]
                if sid in self.task_info:
                    del self.task_info[sid]

# Global task registry
task_registry = TaskRegistry()

def set_process_title(title: str):
    """Set the process title for better Task Manager visibility."""
    try:
        if platform.system() == "Windows" and WINDOWS_AVAILABLE:
            # Set process title using Windows API
            current_pid = os.getpid()
            process = psutil.Process(current_pid)
            
            # Update process name in task manager
            try:
                # Set the process title
                win32api.SetConsoleTitle(title)
            except Exception as e:
                print(f"Could not set console title: {e}")
                
            # Update process description (visible in Task Manager Details tab)
            try:
                # This requires elevated privileges, so we'll just log it
                print(f"Process title set to: {title}")
                print(f"Process ID: {current_pid}")
                print(f"Process name: {process.name()}")
            except Exception as e:
                print(f"Could not update process description: {e}")
                
        elif platform.system() == "Linux":
            # Linux: set process title
            try:
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                libc.prctl(15, title.encode(), 0, 0, 0)  # PR_SET_NAME
            except Exception as e:
                print(f"Could not set Linux process title: {e}")
                
        elif platform.system() == "Darwin":  # macOS
            # macOS: set process title
            try:
                import ctypes
                libc = ctypes.CDLL("libSystem.dylib")
                libc.setproctitle(title.encode())
            except Exception as e:
                print(f"Could not set macOS process title: {e}")
                
    except Exception as e:
        print(f"Error setting process title: {e}")

def create_task_manager_description(strategy_name: str, strategy_id: int, tickers: List[str], 
                                 accounts: List[str], paper_trading: bool, deployment_id: int) -> str:
    """Create a descriptive task manager description."""
    trading_mode = "📝 Paper" if paper_trading else "💰 Live"
    ticker_str = ", ".join(tickers) if tickers else "No tickers"
    account_str = ", ".join(accounts) if accounts else "No accounts"
    
    description = f"Options Strategy: {strategy_name} (ID: {strategy_id}) | {trading_mode} | Tickers: {ticker_str} | Accounts: {account_str} | Deployment: {deployment_id}"
    return description

async def run_strategy(sid: int, strategy_code: str, params: dict):
    """
    Run a strategy asynchronously.
    
    Args:
        sid: Strategy ID
        strategy_code: Python code containing the strategy
        params: Strategy parameters (including paper_trading flag and deployment_id)
    """
    start_time = time.time()
    deployment_id = params.get("deployment_id")
    strategy_name = params.get("strategy_name", f"Strategy-{sid}")
    tickers = params.get("tickers", [])
    accounts = params.get("accounts", [])
    paper_trading = params.get("paper_trading", True)
    
    # Create descriptive process title for Task Manager
    process_title = create_task_manager_description(
        strategy_name, sid, tickers, accounts, paper_trading, deployment_id
    )
    
    # Set the process title
    set_process_title(process_title)
    
    try:
        # Load strategy
        await task_registry.log(sid, "Loading strategy...")
        strategy = load_strategy_from_code(strategy_code)
        await task_registry.log(sid, f"Loaded strategy: {strategy.name}")

        # Get paper trading setting from params (not used to reconnect here)
        trading_type = "paper" if paper_trading else "real"
        
        # Ensure we have a healthy connection using the connection manager
        if not await connection_manager.ensure_connection(trading_type):
            raise RuntimeError(f"Failed to establish {trading_type} trading connection. Check connection status.")

        ib = IBManager.instance().ib  # get the managed connection
        await task_registry.log(sid, f"Using managed IBKR connection via connection manager ({trading_type} trading)")

        # Create log function
        def log(msg: str):
            asyncio.create_task(task_registry.log(sid, msg))

        # Run strategy
        await task_registry.log(sid, f"Starting strategy with params: {json.dumps(params, indent=2)}")
        await strategy.run(ib, params, log)
        await task_registry.log(sid, "Strategy completed successfully")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Update deployment history with completion status
        if deployment_id:
            try:
                # Get account values to calculate PNL
                initial_capital = 0
                final_capital = 0
                
                # Try to get account values from IBKR
                try:
                    for account in accounts:
                        # Get account summary
                        account_values = ib.accountSummary(account)
                        for value in account_values:
                            if value.tag == "NetLiquidation":
                                final_capital += float(value.value)
                                break
                except Exception as e:
                    await task_registry.log(sid, f"Could not fetch account values: {e}")
                
                # Calculate PNL (this is a simplified calculation)
                pnl = final_capital - initial_capital if initial_capital > 0 else None
                pnl_percent = (pnl / initial_capital * 100) if initial_capital > 0 and pnl is not None else None
                
                # Update deployment status
                await update_deployment_status(deployment_id, {
                    "status": "completed",
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "final_capital": final_capital,
                    "execution_time": execution_time
                })
                
            except Exception as e:
                await task_registry.log(sid, f"Error updating deployment status: {e}")

    except asyncio.CancelledError:
        await task_registry.log(sid, "Strategy cancelled")
        
        # Update deployment status to cancelled
        if deployment_id:
            try:
                await update_deployment_status(deployment_id, {
                    "status": "cancelled",
                    "execution_time": time.time() - start_time
                })
            except Exception as e:
                await task_registry.log(sid, f"Error updating deployment status: {e}")
        
        raise
    except Exception as e:
        await task_registry.log(sid, f"Strategy error: {str(e)}")
        
        # Update deployment status to failed
        if deployment_id:
            try:
                await update_deployment_status(deployment_id, {
                    "status": "failed",
                    "error_message": str(e),
                    "execution_time": time.time() - start_time
                })
            except Exception as update_error:
                await task_registry.log(sid, f"Error updating deployment status: {update_error}")
        
        raise
    finally:
        # Reset process title when strategy completes
        set_process_title("Options Trading Strategy Runner (Idle)")
        await task_registry.cleanup(sid)

async def update_deployment_status(deployment_id: int, status_data: dict):
    """Update deployment status in the database."""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://localhost:8000/strategies/api/deployments/{deployment_id}/status",
                json=status_data
            )
            if response.status_code != 200:
                print(f"Failed to update deployment status: {response.text}")
    except Exception as e:
        print(f"Error updating deployment status: {e}")

async def start_strategy(sid: int, strategy_code: str, params: dict) -> asyncio.Task:
    """
    Start a strategy and return the task.
    
    Args:
        sid: Strategy ID
        strategy_code: Python code containing the strategy
        params: Strategy parameters
        
    Returns:
        asyncio.Task: The running task
    """
    # Create task metadata for Task Manager visibility
    task_info = {
        "strategy_id": sid,
        "strategy_name": params.get("strategy_name", f"Strategy-{sid}"),
        "tickers": params.get("tickers", []),
        "accounts": params.get("accounts", []),
        "paper_trading": params.get("paper_trading", True),
        "deployment_id": params.get("deployment_id"),
        "start_time": datetime.now().isoformat(),
        "task_id": f"Task-{sid}-{params.get('deployment_id', 0)}",  # Use unique task identifier
        "process_id": os.getpid(),  # Use actual system process ID
        "task_manager_description": create_task_manager_description(
            params.get("strategy_name", f"Strategy-{sid}"),
            sid,
            params.get("tickers", []),
            params.get("accounts", []),
            params.get("paper_trading", True),
            params.get("deployment_id", 0)
        )
    }
    
    task = asyncio.create_task(run_strategy(sid, strategy_code, params))
    await task_registry.add(sid, task, task_info)
    return task

def get_task_manager_info() -> dict:
    """Get information about all running tasks for Task Manager visibility."""
    running_tasks = task_registry.get_all_running_tasks()
    
    task_info = {
        "total_running": len(running_tasks),
        "tasks": {}
    }
    
    for sid, info in running_tasks.items():
        task_info["tasks"][sid] = {
            "strategy_id": sid,  # Add the strategy_id field
            "strategy_name": info.get("strategy_name", f"Strategy-{sid}"),
            "tickers": info.get("tickers", []),
            "accounts": info.get("accounts", []),
            "paper_trading": info.get("paper_trading", True),
            "deployment_id": info.get("deployment_id"),
            "start_time": info.get("start_time"),
            "task_id": info.get("task_id"),
            "process_id": info.get("process_id"),
            "task_manager_description": info.get("task_manager_description", ""),
            "status": "running"
        }
    
    return task_info
