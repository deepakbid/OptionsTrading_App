"""
Moving Average Crossover Strategy
A self-contained strategy that trades based on moving average crossovers.
"""

from strategies.base import Strategy
from ib_async import IB, Stock, MarketOrder, util
from ib_async.objects import BarData
from datetime import datetime, timezone, timedelta
import asyncio
import numpy as np

class MovingAverageCrossoverStrategy(Strategy):
    """
    Moving Average Crossover Strategy
    
    Buys when fast MA crosses above slow MA, sells when it crosses below.
    """
    
    name = "MovingAverageCrossover"
    
    async def run(self, ib, params, log):
        """
        Main strategy execution method called by the strategy runner
        """
        log(f"Starting {self.name} strategy...")
        log(f"Parameters: {params}")
        
        # Get strategy parameters
        tickers = params.get('tickers', ['SPY'])
        accounts = params.get('accounts', [])
        paper_trading = params.get('paper_trading', True)
        fast_period = params.get('fast_period', 10)
        slow_period = params.get('slow_period', 20)
        
        log(f"Tickers: {tickers}")
        log(f"Accounts: {accounts}")
        log(f"Fast Period: {fast_period}, Slow Period: {slow_period}")
        
        if not accounts:
            log("No accounts provided, cannot run strategy")
            return False
            
        # Use first ticker for now (can be extended to handle multiple)
        ticker = tickers[0].upper()
        account = accounts[0]
        
        log(f"Running strategy on {ticker} for account {account}")
        
        try:
            # Create the strategy instance
            strategy = MovingAverageCrossover(
                ib, ticker, account, fast_period, slow_period
            )
            
            # Run for a limited time (e.g., 1 hour) to demonstrate
            log(f"Strategy started, running for 1 hour...")
            await asyncio.sleep(3600)  # Run for 1 hour
            
            # Stop the strategy
            strategy.stop()
            log(f"{self.name} strategy completed successfully!")
            return True
            
        except Exception as e:
            log(f"Error running strategy: {e}")
            return False


class MovingAverageCrossover:
    """
    Moving Average Crossover Strategy Implementation
    """

    def __init__(self, ib: IB, ticker: str = "SPY", account: str = None, 
                 fast_period: int = 10, slow_period: int = 20):
        self.ib = ib
        self.ticker = ticker.upper()
        self.account = account
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.in_trade = False
        self.position = 0
        self.entry_price = None
        
        if not self.ib.isConnected():
            print("⚠️ IB is not connected. Connect before constructing the strategy.")
            
        # Underlying stock
        self.underlying = Stock(self.ticker, 'SMART', 'USD')
        self.ib.qualifyContracts(self.underlying)
        
        # Historical bars for calculating moving averages
        self.bars = self.ib.reqHistoricalData(
            self.underlying,
            endDateTime='',
            durationStr='30 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            keepUpToDate=True,
            formatDate=1
        )
        
        # Set up bar update handler
        self.bars.updateEvent += self.on_bar_update
        
        log(f"Moving Average Crossover strategy initialized for {ticker}")
        log(f"Fast MA: {fast_period}, Slow MA: {slow_period}")
    
    def on_bar_update(self, bars, has_new_bar):
        """Handle new bar updates"""
        if has_new_bar and len(bars) >= self.slow_period:
            self.check_signals()
    
    def check_signals(self):
        """Check for moving average crossover signals"""
        if len(self.bars) < self.slow_period:
            return
            
        # Calculate moving averages
        closes = [bar.close for bar in self.bars]
        fast_ma = np.mean(closes[-self.fast_period:])
        slow_ma = np.mean(closes[-self.slow_period:])
        
        # Previous values for crossover detection
        if len(closes) >= self.slow_period + 1:
            prev_fast_ma = np.mean(closes[-(self.fast_period+1):-1])
            prev_slow_ma = np.mean(closes[-(self.slow_period+1):-1])
            
            # Check for crossover
            if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
                # Golden cross - buy signal
                if not self.in_trade:
                    self.buy()
            elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
                # Death cross - sell signal
                if self.in_trade:
                    self.sell()
    
    def buy(self):
        """Execute buy order"""
        try:
            order = MarketOrder('BUY', 100)  # Buy 100 shares
            trade = self.ib.placeOrder(self.underlying, order)
            self.ib.sleep(1)  # Wait for order to be processed
            
            if trade.orderStatus.status == 'Filled':
                self.in_trade = True
                self.position = 100
                self.entry_price = trade.orderStatus.avgFillPrice
                log(f"BUY order filled: {self.position} shares at ${self.entry_price:.2f}")
            else:
                log(f"BUY order failed: {trade.orderStatus.status}")
                
        except Exception as e:
            log(f"Error executing buy order: {e}")
    
    def sell(self):
        """Execute sell order"""
        try:
            order = MarketOrder('SELL', self.position)
            trade = self.ib.placeOrder(self.underlying, order)
            self.ib.sleep(1)  # Wait for order to be processed
            
            if trade.orderStatus.status == 'Filled':
                exit_price = trade.orderStatus.avgFillPrice
                pnl = (exit_price - self.entry_price) * self.position
                log(f"SELL order filled: {self.position} shares at ${exit_price:.2f}")
                log(f"P&L: ${pnl:.2f}")
                
                self.in_trade = False
                self.position = 0
                self.entry_price = None
            else:
                log(f"SELL order failed: {trade.orderStatus.status}")
                
        except Exception as e:
            log(f"Error executing sell order: {e}")
    
    def stop(self):
        """Stop the strategy and close any open positions"""
        if self.in_trade:
            log("Closing open position before stopping...")
            self.sell()
        
        # Disconnect from bar updates
        if hasattr(self, 'bars') and self.bars:
            self.bars.updateEvent -= self.on_bar_update
        
        log("Moving Average Crossover strategy stopped")


# Helper function for logging
def log(message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
