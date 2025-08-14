import asyncio
import subprocess
import signal
import platform
import psutil
import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

class RunnerService:
    """Supervisor service for managing strategy processes"""
    
    def __init__(self, db_url: str = None):
        # Use environment variables or default PostgreSQL connection
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://localhost/options_trading')
        self.running_processes: Dict[int, subprocess.Popen] = {}
        self.process_info: Dict[int, Dict] = {}
        self.running = True
        
    def get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(self.db_url)
    
    def create_tables(self):
        """Create new tables for process management"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id SERIAL PRIMARY KEY,
                strategy_id INTEGER NOT NULL,
                requested_by TEXT,
                cfg JSONB DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                pid INTEGER,
                host TEXT,
                started_at TIMESTAMPTZ,
                stopped_at TIMESTAMPTZ,
                last_heartbeat TIMESTAMPTZ,
                exit_code INTEGER,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create run_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_events (
                id SERIAL PRIMARY KEY,
                run_id INTEGER NOT NULL,
                ts TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_heartbeat ON runs(last_heartbeat)")
        
        conn.commit()
        conn.close()
        print("✅ Runner service tables created")
    
    def add_event(self, run_id: int, level: str, message: str):
        """Add event to run_events table"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO run_events (run_id, level, message) VALUES (?, ?, ?)",
            (run_id, level, message)
        )
        conn.commit()
        conn.close()
    
    def update_run_status(self, run_id: int, status: str, **kwargs):
        """Update run status and other fields"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                fields.append(f"{key} = %s")
                values.append(value)
        
        if fields:
            fields.append("status = %s")
            fields.append("updated_at = %s")
            values.extend([status, datetime.now()])
            
            query = f"UPDATE runs SET {', '.join(fields)} WHERE id = %s"
            values.append(run_id)
            cursor.execute(query, values)
        else:
            cursor.execute(
                "UPDATE runs SET status = %s, updated_at = %s WHERE id = %s",
                (status, datetime.now(), run_id)
            )
        
        conn.commit()
        conn.close()
    
    def get_pending_runs(self) -> List[Dict]:
        """Get all pending runs"""
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM runs WHERE status = 'pending'")
        
        runs = cursor.fetchall()
        # Convert RealDictRow to regular dict and handle JSONB
        runs = [dict(run) for run in runs]
        for run in runs:
            # JSONB is already parsed by psycopg2
            if run['cfg'] is None:
                run['cfg'] = {}
        
        conn.close()
        return runs
    
    def claim_run(self, run_id: int) -> bool:
        """Atomically claim a pending run"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE runs SET status = 'starting', updated_at = %s WHERE id = %s AND status = 'pending'",
            (datetime.now(), run_id)
        )
        
        claimed = cursor.rowcount > 0
        if claimed:
            conn.commit()
            self.add_event(run_id, "info", "Run claimed by runner service")
        
        conn.close()
        return claimed
    
    def launch_strategy(self, run: Dict) -> Optional[int]:
        """Launch a strategy process"""
        try:
            # Prepare environment
            env = os.environ.copy()
            cfg = run.get('cfg', {})
            for key, value in cfg.items():
                env[key.upper()] = str(value)
            
            # Add strategy-specific environment
            env['STRATEGY_ID'] = str(run['strategy_id'])
            env['RUN_ID'] = str(run['id'])
            env['STRATEGY_NAME'] = run.get('strategy_name', 'Unknown')
            
            # Create log directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"run_{run['id']}.log"
            
            # Launch process
            if platform.system() == "Windows":
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                process = subprocess.Popen(
                    [sys.executable, "-m", "strategies.runner", "--run-id", str(run['id'])],
                    env=env,
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT,
                    creationflags=CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    [sys.executable, "-m", "strategies.runner", "--run-id", str(run['id'])],
                    env=env,
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            pid = process.pid
            self.running_processes[run['id']] = process
            self.process_info[run['id']] = {
                'pid': pid,
                'started_at': datetime.now(),
                'log_file': str(log_file)
            }
            
            # Update database
            self.update_run_status(
                run['id'], 
                'running',
                pid=pid,
                host=platform.node(),
                started_at=datetime.now()
            )
            
            self.add_event(run['id'], "info", f"Strategy process started with PID {pid}")
            print(f"✅ Launched strategy {run['id']} with PID {pid}")
            return pid
            
        except Exception as e:
            self.add_event(run['id'], "error", f"Failed to launch strategy: {str(e)}")
            self.update_run_status(run['id'], 'error', exit_code=1)
            print(f"❌ Failed to launch strategy {run['id']}: {e}")
            return None
    
    def stop_strategy(self, run_id: int, grace_period: int = 20) -> bool:
        """Stop a running strategy gracefully"""
        if run_id not in self.running_processes:
            return False
        
        try:
            process = self.running_processes[run_id]
            self.update_run_status(run_id, 'stopping')
            self.add_event(run_id, "info", f"Stopping strategy (grace period: {grace_period}s)")
            
            # Send termination signal
            if platform.system() == "Windows":
                # Windows: GenerateConsoleCtrlEvent for graceful shutdown
                try:
                    import win32api
                    import win32con
                    win32api.GenerateConsoleCtrlEvent(win32con.CTRL_BREAK_EVENT, process.pid)
                except ImportError:
                    process.terminate()
            else:
                # Unix: Send SIGTERM
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=grace_period)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                # Force kill if grace period exceeded
                self.add_event(run_id, "warn", f"Grace period exceeded, force killing process")
                if platform.system() == "Windows":
                    process.kill()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
                exit_code = -1
            
            # Cleanup
            del self.running_processes[run_id]
            if run_id in self.process_info:
                del self.process_info[run_id]
            
            # Update database
            self.update_run_status(
                run_id, 
                'stopped',
                stopped_at=datetime.now(),
                exit_code=exit_code
            )
            
            self.add_event(run_id, "info", f"Strategy stopped with exit code {exit_code}")
            print(f"✅ Stopped strategy {run_id}")
            return True
            
        except Exception as e:
            self.add_event(run_id, "error", f"Error stopping strategy: {str(e)}")
            self.update_run_status(run_id, 'error')
            print(f"❌ Error stopping strategy {run_id}: {e}")
            return False
    
    def check_heartbeats(self):
        """Check for stale heartbeats and mark dead processes"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Find runs with stale heartbeats (more than 30 seconds old)
        stale_threshold = datetime.now() - timedelta(seconds=30)
        cursor.execute(
            "SELECT id, pid FROM runs WHERE status = 'running' AND (last_heartbeat IS NULL OR last_heartbeat < %s)",
            (stale_threshold,)
        )
        
        stale_runs = cursor.fetchall()
        for run_id, pid in stale_runs:
            if pid and not psutil.pid_exists(pid):
                # Process is dead
                self.update_run_status(run_id, 'dead', exit_code=-1)
                self.add_event(run_id, "error", "Process died unexpectedly")
                print(f"⚠️ Process {run_id} (PID {pid}) is dead")
                
                # Cleanup if still in memory
                if run_id in self.running_processes:
                    del self.running_processes[run_id]
                if run_id in self.process_info:
                    del self.process_info[run_id]
        
        conn.close()
    
    def monitor_processes(self):
        """Monitor running processes and update status"""
        for run_id, process in list(self.running_processes.items()):
            if process.poll() is not None:
                # Process has finished
                exit_code = process.returncode
                self.update_run_status(
                    run_id, 
                    'stopped',
                    stopped_at=datetime.now(),
                    exit_code=exit_code
                )
                
                if exit_code == 0:
                    self.add_event(run_id, "info", "Strategy completed successfully")
                else:
                    self.add_event(run_id, "error", f"Strategy failed with exit code {exit_code}")
                
                # Cleanup
                del self.running_processes[run_id]
                if run_id in self.process_info:
                    del self.process_info[run_id]
                
                print(f"📋 Strategy {run_id} finished with exit code {exit_code}")
    
    async def run(self):
        """Main runner loop"""
        print("🚀 Starting Runner Service...")
        self.create_tables()
        
        while self.running:
            try:
                # Check for pending runs
                pending_runs = self.get_pending_runs()
                for run in pending_runs:
                    if self.claim_run(run['id']):
                        self.launch_strategy(run)
                
                # Monitor existing processes
                self.monitor_processes()
                
                # Check heartbeats
                self.check_heartbeats()
                
                # Wait before next iteration
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                print("\n🛑 Shutting down Runner Service...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Runner Service error: {e}")
                await asyncio.sleep(5)
        
        # Cleanup: stop all running processes
        for run_id in list(self.running_processes.keys()):
            self.stop_strategy(run_id, grace_period=5)
        
        print("✅ Runner Service stopped")

if __name__ == "__main__":
    runner = RunnerService()
    asyncio.run(runner.run())
