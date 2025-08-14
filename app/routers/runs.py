from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json

router = APIRouter(prefix="/runs", tags=["runs"])

# Database connection
def get_db_connection():
    db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/options_trading')
    return psycopg2.connect(db_url)

# Models
class RunCreate(BaseModel):
    strategy_id: int
    cfg: Dict[str, Any] = {}
    notes: Optional[str] = None
    requested_by: Optional[str] = None

class RunUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

# Endpoints
@router.post("/")
async def create_run(run: RunCreate):
    """Create a new run (strategy execution)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO runs (strategy_id, cfg, notes, requested_by, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id
        """, (run.strategy_id, json.dumps(run.cfg), run.notes, run.requested_by))
        
        run_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return {"success": True, "run_id": run_id, "message": "Run created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create run: {str(e)}")

@router.get("/")
async def list_runs(status: Optional[str] = None, limit: int = 100):
    """List all runs with optional status filter"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if status:
            cursor.execute("""
                SELECT * FROM runs WHERE status = %s 
                ORDER BY created_at DESC LIMIT %s
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM runs 
                ORDER BY created_at DESC LIMIT %s
            """, (limit,))
        
        runs = cursor.fetchall()
        conn.close()
        
        # Convert RealDictRow to regular dict
        return {"runs": [dict(run) for run in runs]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")

@router.get("/{run_id}")
async def get_run(run_id: int):
    """Get details of a specific run"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM runs WHERE id = %s", (run_id,))
        run = cursor.fetchone()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        conn.close()
        return {"run": dict(run)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run: {str(e)}")

@router.post("/{run_id}/stop")
async def stop_run(run_id: int, grace: int = 20):
    """Stop a running strategy with grace period"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if run exists and is running
        cursor.execute("SELECT status FROM runs WHERE id = %s", (run_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Run not found")
        
        if result[0] not in ['running', 'starting']:
            raise HTTPException(status_code=400, detail=f"Cannot stop run with status: {result[0]}")
        
        # Update status to stopping
        cursor.execute("""
            UPDATE runs SET status = 'stopping', updated_at = %s 
            WHERE id = %s
        """, (datetime.now(), run_id))
        
        conn.commit()
        conn.close()
        
        # Note: The actual process termination is handled by the Runner Service
        # This endpoint just marks the run for stopping
        
        return {
            "success": True, 
            "message": f"Run {run_id} marked for stopping (grace period: {grace}s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop run: {str(e)}")

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: int, tail: int = 1000):
    """Get logs for a specific run"""
    try:
        # Check if run exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM runs WHERE id = %s", (run_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Run not found")
        conn.close()
        
        # Read log file
        log_file = f"logs/run_{run_id}.log"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "No log file found"}
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Return last N lines
        logs = lines[-tail:] if len(lines) > tail else lines
        return {"logs": logs, "total_lines": len(lines)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.get("/{run_id}/events")
async def get_run_events(run_id: int, limit: int = 100):
    """Get events for a specific run"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM run_events 
            WHERE run_id = %s 
            ORDER BY ts DESC 
            LIMIT %s
        """, (run_id, limit))
        
        events = cursor.fetchall()
        conn.close()
        
        return {"events": [dict(event) for event in events]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")

@router.delete("/{run_id}")
async def delete_run(run_id: int):
    """Delete a run and its associated data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if run exists
        cursor.execute("SELECT status FROM runs WHERE id = %s", (run_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Run not found")
        
        if result[0] in ['running', 'starting', 'stopping']:
            raise HTTPException(status_code=400, detail="Cannot delete running run")
        
        # Delete run and associated events
        cursor.execute("DELETE FROM run_events WHERE run_id = %s", (run_id,))
        cursor.execute("DELETE FROM runs WHERE id = %s", (run_id,))
        
        conn.commit()
        conn.close()
        
        # Delete log file if it exists
        log_file = f"logs/run_{run_id}.log"
        if os.path.exists(log_file):
            os.remove(log_file)
        
        return {"success": True, "message": f"Run {run_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete run: {str(e)}")

# Dashboard endpoints
@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM runs 
            GROUP BY status
        """)
        
        status_counts = dict(cursor.fetchall())
        
        # Get recent activity
        cursor.execute("""
            SELECT COUNT(*) as total_runs,
                   COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as runs_24h,
                   COUNT(CASE WHEN status = 'running' THEN 1 END) as currently_running
            FROM runs
        """)
        
        activity = cursor.fetchone()
        
        conn.close()
        
        return {
            "status_counts": status_counts,
            "total_runs": activity[0],
            "runs_24h": activity[1],
            "currently_running": activity[2]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")
