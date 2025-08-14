"""
Seed strategy for testing the application.
"""
from strategies.base import Strategy
import asyncio

class Hello(Strategy):
    name = "Hello Logger"
    
    async def run(self, ib, params, log):
        log("Starting Hello strategy...")
        await asyncio.sleep(1.5)
        log("Hello from the strategy!")
        log(f"Received parameters: {params}")
        await asyncio.sleep(1)
        log("Strategy completed successfully!")
