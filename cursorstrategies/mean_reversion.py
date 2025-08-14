"""
Mean Reversion Strategy
A self-contained strategy that trades based on price deviations from moving averages.
"""

from strategies.base import Strategy
from ib_async import IB, Stock, MarketOrder, util
from ib_async.objects import BarData
from datetime import datetime, timezone, timedelta
import asyncio
import numpy as np

class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strategy
    
    Buys when price is significantly below moving average, sells when above.
    """
    
    name = "MeanReversion"
    
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
        ma_period = params.get('ma_period', 20)
        deviation_threshold = params.get('deviation_threshold', 2.0)  # Standard deviations
        
        log(f"Tickers: {tickers}")
        log(f"Accounts: {accounts}")
        log(f"MA Period: {ma_period}, Deviation Threshold: {deviation_threshold}")
        
        if not accounts:
            log("No accounts provided, cannot run strategy")
            return False
            
        # Use first ticker for now (can be extended to handle multiple)
        ticker = tickers[0].upper()
        account = accounts[0]
        
        log(f"Running strategy on {ticker} for account {account}")
        
        try:
            # Create the strategy instance
            strategy = MeanReversion(
                ib, ticker, account, ma_period, deviation_threshold
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


class MeanReversion:
    """
    Mean Reversion Strategy Implementation
    """

    def __init__(self, ib: IB, ticker: str = "SPY", account: str = None, 
                 ma_period: int = 20, deviation_threshold: float = 2.0):
        self.ib = ib
        self.ticker = ticker.upper()
        self.account = account
        self.ma_period = ma_period
        self.deviation_threshold = deviation_threshold
        self.in_trade = False
        self.position = 0
        self.entry_price = None
        self.entry_time = None
        
        if not self.ib.isConnected():
            print("⚠️ IB is not connected. Connect before constructing the strategy.")
            
        # Underlying stock
        self.underlying = Stock(self.ticker, 'SMART', 'USD')
        self.ib.qualifyContracts(self.underlying)
        
        # Historical bars for calculating moving averages and volatility
        self.bars = self.ib.reqHistoricalData(
            self.underlying,
            endDateTime='',
            durationStr='60 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            keepUpToDate=True,
            formatDate=1
        )
        
        # Set up bar update handler
        self.bars.updateEvent += self.on_bar_update
        
        log(f"Mean Reversion strategy initialized for {ticker}")
        log(f"MA Period: {ma_period}, Deviation Threshold: {deviation_threshold}")
    
    def on_bar_update(self, bars, has_new_bar):
        """Handle new bar updates"""
        if has_new_bar and len(bars) >= self.ma_period:
            self.check_signals()
    
    def check_signals(self):
        """Check for mean reversion signals"""
        if len(self.bars) < self.ma_period:
            return
            
        # Calculate moving average and standard deviation
        closes = [bar.close for bar in self.bars]
        current_price = closes[-1]
        ma = np.mean(closes[-self.ma_period:])
        std = np.std(closes[-self.ma_period:])
        
        # Calculate z-score (how many standard deviations from mean)
        z_score = (current_price - ma) / std if std > 0 else 0
        
        log(f"Current Price: ${current_price:.2f}, MA: ${ma:.2f}, Z-Score: {z_score:.2f}")
        
        # Check for entry signals
        if not self.in_trade:
            if z_score < -self.deviation_threshold:
                # Price significantly below mean - buy signal
                self.buy()
            elif z_score > self.deviation_threshold:
                # Price significantly above mean - short signal (if supported)
                log(f"Short signal detected (Z-Score: {z_score:.2f}) but shorting not implemented")
        
        # Check for exit signals
        elif self.in_trade:
            # Exit when price returns to mean (z-score approaches 0)
            if abs(z_score) < 0.5:  # Close to mean
                self.sell()
            # Stop loss if price moves further away
            elif z_score < -self.deviation_threshold * 1.5:
                log(f"Stop loss triggered (Z-Score: {z_score:.2f})")
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
                self.entry_time = datetime.now()
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
                hold_time = datetime.now() - self.entry_time if self.entry_time else timedelta(0)
                
                log(f"SELL order filled: {self.position} shares at ${exit_price:.2f}")
                log(f"P&L: ${pnl:.2f}, Hold Time: {hold_time}")
                
                self.in_trade = False
                self.position = 0
                self.entry_price = None
                self.entry_time = None
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
        
        log("Mean Reversion strategy stopped")


# Helper function for logging
def log(message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
