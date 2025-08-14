"""
Strategies router for managing and running strategies.
"""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from ..db import get_session
from ..models import DeploymentHistory
from ..runner import task_registry, start_strategy
from ..file_strategy_loader import file_strategy_loader
from ..ib_adapter import IBManager

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session: AsyncSession = Depends(get_session)):
    """Show strategies list and add form."""
    # Get all strategies from files
    strategies = []
    for filename in file_strategy_loader.get_strategy_files():
        strategy_info = file_strategy_loader.get_strategy_info(filename)
        if strategy_info:
            strategies.append(strategy_info)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "strategies": strategies
    })

@router.get("/api/strategies", response_class=JSONResponse)
async def list_strategies_api(session: AsyncSession = Depends(get_session)):
    """Get all strategies as JSON."""
    strategies = []
    for filename in file_strategy_loader.get_strategy_files():
        strategy_info = file_strategy_loader.get_strategy_info(filename)
        if strategy_info:
            strategies.append({
                "id": filename,  # Use filename as ID
                "name": strategy_info["name"],
                "description": strategy_info["description"],
                "code": strategy_info["code"],
                "createdAt": filename,  # Use filename as timestamp for now
                "winRate": 0,
                "allocation": 0,
                "filename": filename
            })
    
    return strategies

@router.get("/api/strategies/{filename}", response_class=JSONResponse)
async def get_strategy_api(filename: str, session: AsyncSession = Depends(get_session)):
    """Get a specific strategy by filename."""
    strategy_info = file_strategy_loader.get_strategy_info(filename)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return {
        "id": filename,
        "name": strategy_info["name"],
        "description": strategy_info["description"],
        "code": strategy_info["code"],
        "createdAt": filename,
        "winRate": 0,
        "allocation": 0,
        "filename": filename
    }

@router.delete("/api/strategies/{filename}", response_class=JSONResponse)
async def delete_strategy_api(filename: str, session: AsyncSession = Depends(get_session)):
    """Delete a strategy file."""
    success = file_strategy_loader.delete_strategy_file(filename)
    
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found or could not be deleted")
    
    return {"success": True, "message": f"Strategy {filename} deleted successfully"}

@router.put("/api/strategies/{filename}", response_class=JSONResponse)
async def update_strategy_api(
    filename: str,
    name: str = Form(...),
    description: str = Form(""),
    code: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    """Update an existing strategy file."""
    try:
        success = file_strategy_loader.update_strategy_file(filename, description, code)
        
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found or could not be updated")
        
        # Get updated strategy info for response
        strategy_info = file_strategy_loader.get_strategy_info(filename)
        
        return {
            "id": filename,
            "name": strategy_info["name"],
            "description": strategy_info["description"],
            "code": strategy_info["code"],
            "createdAt": filename,
            "winRate": 0,
            "allocation": 0,
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update strategy: {str(e)}")

@router.get("/api/accounts", response_class=JSONResponse)
async def get_accounts_api(paper_trading: bool = Query(True, description="Whether to get paper trading accounts")):
    """Get all available account numbers from TWS for paper or real trading."""
    try:
        ib_manager = IBManager.instance()
        accounts = await ib_manager.get_accounts(paper_trading=paper_trading)
        return {
            "accounts": accounts, 
            "status": "success",
            "trading_type": "paper" if paper_trading else "real"
        }
    except Exception as e:
        # Return default accounts if connection fails
        default_accounts = ["DU1234567", "DU1234568"] if paper_trading else ["REAL1234567", "REAL1234568"]
        return {
            "accounts": default_accounts,
            "status": "fallback",
            "trading_type": "paper" if paper_trading else "real",
            "error": str(e)
        }

@router.get("/api/accounts/all", response_class=JSONResponse)
async def get_all_accounts_api():
    """Get all available account numbers from TWS for both paper and real trading."""
    try:
        ib_manager = IBManager.instance()
        all_accounts = await ib_manager.get_all_accounts()
        return {
            "accounts": all_accounts,
            "status": "success"
        }
    except Exception as e:
        # Return default accounts if connection fails
        return {
            "accounts": {
                "paper": ["DU1234567", "DU1234568"],
                "real": ["REAL1234567", "REAL1234568"]
            },
            "status": "fallback",
            "error": str(e)
        }

@router.post("/create")
async def create_strategy(
    name: str = Form(...),
    description: str = Form(""),
    code: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    """Create a new strategy."""
    try:
        # Create strategy file
        filename = file_strategy_loader.create_strategy_file(name, description, code)
        
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid strategy code: {str(e)}")

@router.post("/api/strategies", response_class=JSONResponse)
async def create_strategy_api(
    name: str = Form(...),
    description: str = Form(""),
    code: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    """Create a new strategy via API."""
    try:
        print(f"Creating strategy: {name}")
        print(f"Description: {description}")
        print(f"Code length: {len(code)}")
        print(f"Code preview: {code[:200]}...")
        
        # Create strategy file
        filename = file_strategy_loader.create_strategy_file(name, description, code)
        print(f"Strategy file created: {filename}")
        
        # Get strategy info for response
        strategy_info = file_strategy_loader.get_strategy_info(filename)
        
        return {
            "id": filename,
            "name": strategy_info["name"],
            "description": strategy_info["description"],
            "code": strategy_info["code"],
            "createdAt": filename,
            "winRate": 0,
            "allocation": 0,
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error creating strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create strategy: {str(e)}")

@router.post("/", response_class=JSONResponse)
async def create_trading_strategy(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Create a new trading strategy."""
    try:
        data = await request.json()
        
        # Create new strategy file
        filename = file_strategy_loader.create_strategy_file(
            data.get("name", "New Strategy"),
            data.get("tickers", "TBD"),
            data.get("pythonCode", "# Your Python strategy code here")
        )
        
        # Get strategy info for response
        strategy_info = file_strategy_loader.get_strategy_info(filename)
        
        return {
            "id": filename,
            "name": strategy_info["name"],
            "description": strategy_info["description"],
            "code": strategy_info["code"],
            "createdAt": filename,
            "winRate": 0,
            "allocation": 0,
            "filename": filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create strategy: {str(e)}")

@router.put("/{sid}", response_class=JSONResponse)
async def update_strategy(
    sid: str,  # Now it's a filename
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Update an existing trading strategy."""
    try:
        # Get update data from request
        data = await request.json()
        
        # Update strategy file
        success = file_strategy_loader.update_strategy_file(
            sid,  # filename
            data.get("tickers", ""),
            data.get("pythonCode", "")
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found or could not be updated")
        
        # Get updated strategy info for response
        strategy_info = file_strategy_loader.get_strategy_info(sid)
        
        return {
            "id": sid,
            "name": strategy_info["name"],
            "description": strategy_info["description"],
            "code": strategy_info["code"],
            "createdAt": sid,
            "winRate": 0,
            "allocation": 0,
            "filename": sid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update strategy: {str(e)}")

@router.delete("/{sid}")
async def delete_strategy(sid: str, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Delete a strategy."""
    # Cancel if running
    if task_registry.is_running(sid):
        await task_registry.cancel(sid)
    
    # Delete strategy file
    success = file_strategy_loader.delete_strategy_file(sid)
    
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found or could not be deleted")
    
    return {"message": "Strategy deleted successfully", "id": sid}

@router.get("/api/strategies/{sid}", response_class=JSONResponse)
async def get_strategy_api(sid: str, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Get a strategy by filename as JSON."""
    strategy_info = file_strategy_loader.get_strategy_info(sid)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return {
        "id": sid,
        "name": strategy_info["name"],
        "description": strategy_info["description"],
        "code": strategy_info["code"],
        "createdAt": sid,
        "winRate": 0,
        "allocation": 0,
        "filename": sid
    }

@router.get("/detail/{sid}", response_class=HTMLResponse)
async def strategy_detail(sid: str, request: Request, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Show strategy details and logs."""
    strategy_info = file_strategy_loader.get_strategy_info(sid)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Create a strategy object with the expected attributes
    class StrategyObject:
        def __init__(self, info):
            self.id = info["filename"]
            self.name = info["name"]
            self.description = info["description"]
            self.code = info["code"]
    
    strategy = StrategyObject(strategy_info)
    is_running = task_registry.is_running(sid)
    logs = task_registry.get_logs(sid)
    
    return templates.TemplateResponse("strategy_detail.html", {
        "request": request,
        "strategy": strategy,
        "is_running": is_running,
        "logs": logs
    })

@router.post("/run/{sid}")
async def run_strategy_endpoint(
    sid: str,  # Now it's a filename
    params: str = Form("{}"),
    accounts: str = Form("DU1234567"),
    instrument: str = Form("SPX"),
    paper_trading: bool = Form(True),
    session: AsyncSession = Depends(get_session)
):
    """Run a strategy with parameters."""
    strategy_info = file_strategy_loader.get_strategy_info(sid)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if task_registry.is_running(sid):
        raise HTTPException(status_code=400, detail="Strategy is already running")
    
    try:
        # Parse parameters
        if isinstance(params, str):
            params_dict = json.loads(params)
        else:
            params_dict = params
        
        # Parse accounts (comma-separated string to list)
        if isinstance(accounts, str):
            accounts_list = [acc.strip() for acc in accounts.split(",") if acc.strip()]
        else:
            accounts_list = [accounts] if not isinstance(accounts, list) else accounts
        
        # Add accounts, instrument, and trading type to params
        params_dict["accounts"] = accounts_list
        params_dict["instrument"] = instrument
        params_dict["paper_trading"] = paper_trading
        
        # Start the strategy
        await start_strategy(sid, strategy_info["code"], params_dict)
        
        return RedirectResponse(url=f"/strategies/detail/{sid}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to run strategy: {str(e)}")

@router.post("/api/strategies/{sid}/deploy", response_class=JSONResponse)
async def deploy_strategy_api(
    sid: str, request: Request, session: AsyncSession = Depends(get_session)  # Now it's a filename
):
    """Deploy a strategy to selected accounts."""
    try:
        body = await request.json()
        selected_accounts = body.get("selected_accounts", [])
        paper_trading = body.get("paper_trading", True)
        tickers = body.get("tickers", "")
        
        print(f"DEBUG: Deploying strategy {sid} with accounts: {selected_accounts}, paper_trading: {paper_trading}, tickers: {tickers}")
        
        if not tickers or tickers.strip() == "":
            return {"success": False, "error": "No tickers provided. Please enter tickers for the strategy before deploying."}
        
        if not selected_accounts:
            return {"success": False, "error": "No accounts selected. Please select at least one account."}
        
        # Check if strategy is already running on any of the selected accounts
        existing_deployments = await session.execute(
            select(DeploymentHistory).where(
                DeploymentHistory.strategy_id == sid,
                DeploymentHistory.status.in_(["running"])
            )
        )
        existing = existing_deployments.scalars().first()
        if existing:
            # Check if any selected accounts overlap with existing deployment accounts
            existing_accounts = existing.accounts.split(',') if existing.accounts else []
            overlapping_accounts = [acc for acc in selected_accounts if acc in existing_accounts]
            if overlapping_accounts:
                return {
                    "success": False, 
                    "error": f"Strategy is already running on account(s): {', '.join(overlapping_accounts)}. Cannot run the same strategy on the same account simultaneously."
                }
        
        # Get strategy details from file
        strategy_filename = str(sid)  # In file-based system, sid is the filename
        strategy_info = file_strategy_loader.get_strategy_info(strategy_filename)
        
        if not strategy_info:
            return {"success": False, "error": "Strategy not found"}
        
        strategy_name = strategy_info["name"]
        strategy_code = strategy_info["code"]
        
        # Get IBKR connection info
        ib_manager = IBManager.instance()
        if not await ib_manager.is_connected():
            return {"success": False, "error": "IBKR connection not established. Please connect first."}
        
        connection_info = await ib_manager.get_connection_info()
        current_type = connection_info.get('type', 'unknown')
        
        # Validate connection type matches selected mode
        expected_type = 'paper' if paper_trading else 'real'
        
        if current_type != expected_type:
            return {
                "success": False,
                "error": f"Connection type mismatch. Expected {expected_type} trading but connected to {current_type} trading."
            }
        
        # Create deployment history record
        deployment_record = DeploymentHistory(
            strategy_id=sid,
            strategy_name=strategy_name,
            tickers=tickers,
            accounts=",".join(selected_accounts),
            paper_trading=paper_trading,
            status="running",
            deployed_at=datetime.utcnow()
        )
        
        session.add(deployment_record)
        await session.commit()
        await session.refresh(deployment_record)
        
        # Execute the strategy code
        try:
            # Load and validate the strategy code
            strategy_module = file_strategy_loader.load_strategy_from_file(strategy_filename)
            
            if not strategy_module:
                return {"success": False, "error": "Failed to load strategy from file"}
            
            # Create strategy parameters with tickers and accounts
            strategy_params = {
                "strategy_id": sid,
                "strategy_name": strategy_name,
                "accounts": selected_accounts,
                "tickers": [t.strip() for t in tickers.split(',') if t.strip()],  # Convert comma-separated string to list
                "paper_trading": paper_trading,
                "connection_type": current_type,
                "deployment_id": deployment_record.id
            }
            
            print(f"DEBUG: Strategy parameters: {strategy_params}")
            
            # Start the strategy with the code and params
            task = await start_strategy(sid, strategy_code, strategy_params)
            task_id = str(task.get_name()) if hasattr(task, 'get_name') else str(id(task))
            
            return {
                "success": True,
                "message": f"Strategy '{strategy_name}' deployed successfully on accounts: {', '.join(selected_accounts)} with tickers: {tickers}",
                "task_id": task_id,
                "accounts": selected_accounts,
                "tickers": tickers,
                "trading_type": current_type,
                "strategy_id": sid,
                "deployment_id": deployment_record.id
            }
            
        except Exception as e:
            # Update deployment record with error
            deployment_record.status = "failed"
            deployment_record.error_message = str(e)
            await session.commit()
            
            print(f"DEBUG: Error executing strategy code: {e}")
            return {
                "success": False,
                "error": f"Failed to execute strategy code: {str(e)}"
            }
            
    except Exception as e:
        print(f"DEBUG: Deployment error: {e}")
        return {"success": False, "error": f"Deployment failed: {str(e)}"}

@router.get("/api/deployments", response_class=JSONResponse)
async def get_deployment_history(session: AsyncSession = Depends(get_session)):
    """Get deployment history for all strategies."""
    try:
        result = await session.execute(
            select(DeploymentHistory).order_by(DeploymentHistory.deployed_at.desc())
        )
        deployments = result.scalars().all()
        
        return [
            {
                "id": d.id,
                "strategy_id": d.strategy_id,
                "strategy_name": d.strategy_name,
                "tickers": d.tickers,
                "accounts": d.accounts.split(",") if d.accounts else [],
                "paper_trading": d.paper_trading,
                "deployed_at": d.deployed_at.isoformat() if d.deployed_at else None,
                "status": d.status,
                "pnl": d.pnl,
                "pnl_percent": d.pnl_percent,
                "initial_capital": d.initial_capital,
                "final_capital": d.final_capital,
                "execution_time": d.execution_time,
                "error_message": d.error_message
            }
            for d in deployments
        ]
    except Exception as e:
        print(f"Error fetching deployment history: {e}")
        return []

@router.get("/api/deployments/{strategy_id}", response_class=JSONResponse)
async def get_strategy_deployments(strategy_id: int, session: AsyncSession = Depends(get_session)):
    """Get deployment history for a specific strategy."""
    try:
        result = await session.execute(
            select(DeploymentHistory)
            .where(DeploymentHistory.strategy_id == strategy_id)
            .order_by(DeploymentHistory.deployed_at.desc())
        )
        deployments = result.scalars().all()
        
        return [
            {
                "id": d.id,
                "strategy_id": d.strategy_id,
                "strategy_name": d.strategy_name,
                "tickers": d.tickers,
                "accounts": d.accounts.split(",") if d.accounts else [],
                "paper_trading": d.paper_trading,
                "deployed_at": d.deployed_at.isoformat() if d.deployed_at else None,
                "status": d.status,
                "pnl": d.pnl,
                "pnl_percent": d.pnl_percent,
                "initial_capital": d.initial_capital,
                "final_capital": d.final_capital,
                "execution_time": d.execution_time,
                "error_message": d.error_message
            }
            for d in deployments
        ]
    except Exception as e:
        print(f"Error fetching strategy deployments: {e}")
        return []

@router.put("/api/deployments/{deployment_id}/status", response_class=JSONResponse)
async def update_deployment_status(
    deployment_id: int, 
    request: Request, 
    session: AsyncSession = Depends(get_session)
):
    """Update deployment status (called when strategy completes/fails)."""
    try:
        body = await request.json()
        status = body.get("status")
        pnl = body.get("pnl")
        pnl_percent = body.get("pnl_percent")
        final_capital = body.get("final_capital")
        execution_time = body.get("execution_time")
        error_message = body.get("error_message")
        
        result = await session.execute(
            select(DeploymentHistory).where(DeploymentHistory.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()
        
        if not deployment:
            return {"success": False, "error": "Deployment not found"}
        
        # Update fields
        if status:
            deployment.status = status
        if pnl is not None:
            deployment.pnl = pnl
        if pnl_percent is not None:
            deployment.pnl_percent = pnl_percent
        if final_capital is not None:
            deployment.final_capital = final_capital
        if execution_time is not None:
            deployment.execution_time = execution_time
        if error_message is not None:
            deployment.error_message = error_message
        
        await session.commit()
        
        return {"success": True, "message": "Deployment status updated"}
        
    except Exception as e:
        print(f"Error updating deployment status: {e}")
        return {"success": False, "error": str(e)}

@router.post("/api/strategies/{sid}/run", response_class=JSONResponse)
async def run_strategy_api(
    sid: str,  # Now it's a filename
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Run a strategy via API."""
    strategy_info = file_strategy_loader.get_strategy_info(sid)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if task_registry.is_running(sid):
        raise HTTPException(status_code=400, detail="Strategy is already running")
    
    try:
        # Parse JSON body
        body = await request.json()
        params = body.get("params", {})
        accounts = body.get("accounts", ["DU1234567"])  # Default to single account if not provided
        instrument = body.get("instrument", "SPX")
        paper_trading = body.get("paper_trading", True)  # Default to paper trading
        
        # Validate accounts is a list
        if not isinstance(accounts, list):
            accounts = [accounts]
        
        # Add accounts, instrument, and trading type to params
        params["accounts"] = accounts
        params["instrument"] = instrument
        params["paper_trading"] = paper_trading
        
        # Start the strategy
        await start_strategy(sid, strategy_info["code"], params)
        
        return {
            "status": "started", 
            "strategy_id": sid, 
            "accounts": accounts, 
            "instrument": instrument,
            "paper_trading": paper_trading
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to run strategy: {str(e)}")

@router.get("/stop/{sid}")
async def stop_strategy(sid: str, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Stop a running strategy."""
    if not task_registry.is_running(sid):
        raise HTTPException(status_code=400, detail="Strategy is not running")
    
    success = await task_registry.cancel(sid)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop strategy")
    
    return RedirectResponse(url=f"/strategies/detail/{sid}", status_code=303)

@router.get("/api/strategies/{sid}/stop", response_class=JSONResponse)
async def stop_strategy_api(sid: str, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Stop a running strategy via API."""
    if not task_registry.is_running(sid):
        raise HTTPException(status_code=400, detail="Strategy is not running")
    
    success = await task_registry.cancel(sid)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop strategy")
    
    return {"status": "stopped", "strategy_id": sid}

@router.get("/logs/{sid}")
async def get_logs(sid: str, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Get strategy logs."""
    strategy_info = file_strategy_loader.get_strategy_info(sid)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    logs = task_registry.get_logs(sid)
    return "\n".join(logs) if logs else "No logs available."

@router.get("/api/strategies/{sid}/logs", response_class=JSONResponse)
async def get_logs_api(sid: str, session: AsyncSession = Depends(get_session)):  # Now it's a filename
    """Get strategy logs via API."""
    strategy_info = file_strategy_loader.get_strategy_info(sid)
    
    if not strategy_info:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    logs = task_registry.get_logs(sid)
    return {"logs": logs, "strategy_id": sid}

@router.get("/api/tasks/running", response_class=JSONResponse)
async def get_running_tasks_api():
    """Get information about all running tasks for Task Manager visibility."""
    from ..runner import get_task_manager_info
    return get_task_manager_info()

@router.get("/api/tasks/{sid}/info", response_class=JSONResponse)
async def get_task_info_api(sid: str):  # Now it's a filename
    """Get detailed information about a specific running task."""
    from ..runner import task_registry
    task_info = task_registry.get_task_info(sid)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found or not running")
    
    return {
        "task_id": sid,
        "info": task_info,
        "is_running": task_registry.is_running(sid)
    }

@router.post("/api/deployments/{deployment_id}/stop", response_class=JSONResponse)
async def stop_deployment_api(deployment_id: int, session: AsyncSession = Depends(get_session)):
    """Stop a running deployment/strategy."""
    try:
        print(f"Attempting to stop deployment {deployment_id}...")
        
        # Get deployment details
        result = await session.execute(select(DeploymentHistory).where(DeploymentHistory.id == deployment_id))
        deployment = result.scalar_one_or_none()
        
        if not deployment:
            print(f"Deployment {deployment_id} not found")
            return {"success": False, "error": "Deployment not found"}
        
        print(f"Found deployment: {deployment.strategy_name}, status: {deployment.status}")
        
        if deployment.status != "running":
            print(f"Deployment {deployment_id} is not running (status: {deployment.status})")
            return {"success": False, "error": f"Deployment is not running (status: {deployment.status})"}
        
        # Stop the strategy using the strategy ID
        strategy_id = deployment.strategy_id
        print(f"Strategy ID: {strategy_id}")
        
        # Import here to avoid circular imports
        from ..runner import task_registry
        
        # Check if strategy is running in task registry
        is_running = task_registry.is_running(strategy_id)
        print(f"Strategy {strategy_id} running in task registry: {is_running}")
        
        if not is_running:
            # Update deployment status to stopped
            print(f"Strategy {strategy_id} not running, updating deployment status to stopped")
            deployment.status = "stopped"
            await session.commit()
            return {"success": True, "message": "Strategy was not running, marked as stopped"}
        
        # Stop the running strategy
        print(f"Attempting to cancel strategy {strategy_id}...")
        success = await task_registry.cancel(strategy_id)
        print(f"Cancel result: {success}")
        
        if success:
            # Update deployment status
            deployment.status = "stopped"
            await session.commit()
            print(f"Deployment {deployment_id} status updated to stopped")
            return {"success": True, "message": "Strategy stopped successfully"}
        else:
            print(f"Failed to cancel strategy {strategy_id}")
            return {"success": False, "error": "Failed to stop strategy"}
            
    except Exception as e:
        print(f"Error stopping deployment {deployment_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.get("/api/deployments/{deployment_id}/logs", response_class=JSONResponse)
async def get_deployment_logs_api(deployment_id: int, session: AsyncSession = Depends(get_session)):
    """Get logs for a specific deployment."""
    try:
        # Get deployment details from the existing system
        result = await session.execute(select(DeploymentHistory).where(DeploymentHistory.id == deployment_id))
        deployment = result.scalar_one_or_none()
        
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # For now, return deployment information since the old system doesn't have detailed logs
        # This will help you debug deployment failures
        logs = [
            f"=== DEPLOYMENT LOGS ===\n",
            f"Deployment ID: {deployment.id}\n",
            f"Strategy: {deployment.strategy_name}\n",
            f"Status: {deployment.status}\n",
            f"Deployed at: {deployment.deployed_at}\n",
            f"Tickers: {deployment.tickers}\n",
            f"Accounts: {deployment.accounts}\n",
            f"Paper Trading: {deployment.paper_trading}\n",
            f"P&L: {deployment.pnl if deployment.pnl is not None else 'N/A'}\n",
            f"Execution Time: {deployment.execution_time}s" if deployment.execution_time else "N/A\n",
            f"Initial Capital: {deployment.initial_capital if deployment.initial_capital else 'N/A'}\n",
            f"Final Capital: {deployment.final_capital if deployment.final_capital else 'N/A'}\n"
        ]
        
        # Add error message if available
        if hasattr(deployment, 'error_message') and deployment.error_message:
            logs.append(f"Error Message: {deployment.error_message}\n")
        
        logs.extend([
            f"\n=== DEBUGGING INFO ===\n",
            f"Note: Detailed execution logs are not available in the current system.\n",
            f"To get better logging, consider:\n",
            f"1. Adding print() statements to your strategy code\n",
            f"2. Using the new process management system\n",
            f"3. Checking the browser console for JavaScript errors\n",
            f"4. Checking your FastAPI server logs\n"
        ])
        
        return {
            "logs": logs,
            "deployment_id": deployment_id,
            "source": "existing_system"
        }
        
    except Exception as e:
        return {"logs": [f"Error loading logs: {str(e)}"], "deployment_id": deployment_id, "source": "error"}
