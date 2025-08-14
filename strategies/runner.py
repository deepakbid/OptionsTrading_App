#!/usr/bin/env python3
"""
Strategy Runner Shim - Wraps strategies for process management
This is the entrypoint that the Runner Service launches for each strategy
"""

import os
import sys
import signal
import time
import json
import argparse
import psycopg2
from datetime import datetime
from pathlib import Path

# Global flag for graceful shutdown
stopping = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global stopping
    print(f"🛑 Received signal {signum}, initiating graceful shutdown...")
    stopping = True

def update_heartbeat(run_id: int, db_url: str):
    """Update heartbeat in database"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET last_heartbeat = %s WHERE id = %s",
            (datetime.now(), run_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to update heartbeat: {e}")

def main():
    parser = argparse.ArgumentParser(description="Strategy Runner Shim")
    parser.add_argument("--run-id", required=True, type=int, help="Run ID from database")
    parser.add_argument("--db-url", help="Database connection URL")
    args = parser.parse_args()
    
    # Get database URL from environment or argument
    db_url = args.db_url or os.getenv('DATABASE_URL', 'postgresql://localhost/options_trading')
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    if os.name == 'nt':  # Windows
        signal.signal(signal.SIGINT, signal_handler)
    
    print(f"🚀 Starting strategy for run {args.run_id}")
    print(f"📊 Environment: {dict(os.environ)}")
    
    # Get strategy configuration from environment
    strategy_id = os.getenv('STRATEGY_ID')
    strategy_name = os.getenv('STRATEGY_NAME', 'Unknown')
    
    # Start heartbeat loop
    last_heartbeat = time.time()
    heartbeat_interval = 10  # seconds
    
    try:
        # Main strategy loop
        while not stopping:
            current_time = time.time()
            
            # Send heartbeat
            if current_time - last_heartbeat >= heartbeat_interval:
                update_heartbeat(args.run_id, db_url)
                last_heartbeat = current_time
                print(f"💓 Heartbeat sent at {datetime.now()}")
            
            # Here you would normally run your strategy logic
            # For now, just simulate work
            time.sleep(1)
            
        print("✅ Strategy completed gracefully")
        return 0
        
    except KeyboardInterrupt:
        print("🛑 Strategy interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Strategy error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
