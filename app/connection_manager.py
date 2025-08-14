"""
Connection Manager for IBKR Trading
Manages connections to Interactive Brokers with health monitoring and reconnection
"""

from .ib_adapter import IBManager
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os

class ConnectionManager:
    def __init__(self):
        self._started = False
        self._mode = None  # "paper" | "real"

    async def start(self):
        # Marker; never create/set a new loop here.
        self._started = True

    async def ensure_connection(self, mode: str) -> bool:
        """
        mode: "paper" or "real"
        """
        paper = (mode == "paper")
        self._mode = mode

        ib = await IBManager.instance().connect(paper=paper, client_id=19)
        # Smoke test to guarantee we’re on THIS loop:
        try:
            _ = await ib.reqCurrentTimeAsync()
            return True
        except Exception:
            return False

    async def stop(self):
        if not self._started:
            return
        try:
            # Optional: leave IB connected if your app prefers
            await IBManager.instance().disconnect()
        finally:
            self._started = False

connection_manager = ConnectionManager()
