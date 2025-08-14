from abc import ABC, abstractmethod

class Strategy(ABC):
    name: str = "Unnamed Strategy"

    @abstractmethod
    async def run(self, ib, params: dict, log):
        """
        Implement in user code; use ib_insync 'ib' object and 'log(str)'.
        
        Args:
            ib: Connected ib_insync IB instance
            params: Dictionary of strategy parameters
            log: Function to log messages (log(str))
        """
        pass
