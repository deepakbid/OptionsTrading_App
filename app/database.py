from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json

# Database URL
DATABASE_URL = "sqlite:///strategies.db"
engine = create_engine(DATABASE_URL, echo=True)

# Enums
class RunStatus(str, Enum):
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEAD = "dead"

class EventLevel(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"

# Enhanced Models
class Strategy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    code: str
    entrypoint: str = Field(default="python -m strategies.runner --strategy")  # Default entrypoint
    default_env: Dict[str, Any] = Field(default_factory=dict, sa_column_kwargs={"type": "TEXT"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategy.id")
    requested_by: Optional[str] = None
    cfg: Dict[str, Any] = Field(default_factory=dict, sa_column_kwargs={"type": "TEXT"})
    status: RunStatus = Field(default=RunStatus.PENDING, index=True)
    pid: Optional[int] = None
    host: Optional[str] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    exit_code: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RunEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id")
    ts: datetime = Field(default_factory=datetime.utcnow)
    level: EventLevel
    message: str

# Legacy models (keep existing functionality)
class DeploymentHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategy.id")
    strategy_name: str
    tickers: str
    accounts: str
    paper_trading: bool
    deployed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "running"
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    execution_time: Optional[float] = None

def create_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully")

def get_session():
    """Get database session"""
    return Session(engine)

# Helper functions for JSON handling
def dict_to_json(d: Dict[str, Any]) -> str:
    """Convert dict to JSON string for SQLite storage"""
    return json.dumps(d) if d else "{}"

def json_to_dict(s: str) -> Dict[str, Any]:
    """Convert JSON string from SQLite to dict"""
    try:
        return json.loads(s) if s else {}
    except (json.JSONDecodeError, TypeError):
        return {}
