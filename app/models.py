from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class StrategyModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    code: str = Field(description="User-pasted strategy code")

class DeploymentHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategymodel.id", index=True)
    strategy_name: str = Field(index=True)
    tickers: str = Field(description="Comma-separated list of tickers")
    accounts: str = Field(description="Comma-separated list of account IDs")
    paper_trading: bool = Field(default=True)
    deployed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    status: str = Field(default="running", description="running, completed, failed, cancelled")
    pnl: Optional[float] = Field(default=None, description="Profit/Loss from this deployment")
    pnl_percent: Optional[float] = Field(default=None, description="PNL as percentage")
    initial_capital: Optional[float] = Field(default=None, description="Initial capital when deployed")
    final_capital: Optional[float] = Field(default=None, description="Final capital after completion")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    logs: Optional[str] = Field(default=None, description="Execution logs")
