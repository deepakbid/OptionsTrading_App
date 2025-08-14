# app/ib_adapter.py
from typing import Optional
from ib_async import IB

class IBManager:
    _inst: Optional["IBManager"] = None

    def __init__(self):
        self.ib: IB = IB()
        self._connected = False

    @classmethod
    def instance(cls) -> "IBManager":
        if cls._inst is None:
            cls._inst = IBManager()
        return cls._inst

    async def connect(self, host: str = "127.0.0.1", paper: bool = True, client_id: int = 19) -> IB:
        """
        IMPORTANT:
        - Only use async APIs (connectAsync / disconnectAsync).
        - Do not call ib.run(), asyncio.run(), run_until_complete, or nest_asyncio anywhere.
        """
        if self._connected and self.ib.isConnected():
            return self.ib

        port = 7497 if paper else 7496
        await self.ib.connectAsync(host, port, clientId=client_id)
        self._connected = True
        return self.ib

    async def disconnect(self):
        if self._connected:
            try:
                await self.ib.disconnectAsync()
            finally:
                self._connected = False
