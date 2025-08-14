"""
Momentum Strategy
A self-contained strategy that trades based on price momentum indicators.
"""

from strategies.base import Strategy
from ib_async import IB, Stock, MarketOrder, util
from ib_async.objects import BarData
from datetime import datetime, timezone, timedelta
import asyncio
import numpy as np

class MomentumStrategy(Strategy):
    """
    Momentum Strategy
    
    Buys when momentum is strong and positive, sells when momentum weakens.
    """
    
    name = "Momentum"
    
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
        rsi_period = params.get('rsi_period', 14)
        rsi_overbought = params.get('rsi_overbought', 70)
        rsi_oversold = params.get('rsi_oversold', 30)
        momentum_period = params.get('momentum_period', 10)
        
        log(f"Tickers: {tickers}")
        log(f"Accounts: {accounts}")
        log(f"RSI Period: {rsi_period}, Momentum Period: {momentum_period}")
        
        if not accounts:
            log("No accounts provided, cannot run strategy")
            return False
            
        # Use first ticker for now (can be extended to handle multiple)
        ticker = tickers[0].upper()
        account = accounts[0]
        
        log(f"Running strategy on {ticker} for account {account}")
        
        try:
            # Create the strategy instance
            strategy = Momentum(
                ib, ticker, account, rsi_period, rsi_overbought, 
                rsi_oversold, momentum_period
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


class Momentum:
    """
    Momentum Strategy Implementation
    """

    def __init__(self, ib: IB, ticker: str = "SPY", account: str = None, 
                 rsi_period: int = 14, rsi_overbought: float = 70, 
                 rsi_oversold: float = 30, momentum_period: int = 10):
        self.ib = ib
        self.ticker = ticker.upper()
        self.account = account
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.momentum_period = momentum_period
        self.in_trade = False
        self.position = 0
        self.entry_price = None
        self.entry_time = None
        
        if not self.ib.isConnected():
            print("⚠️ IB is not connected. Connect before constructing the strategy.")
            
        # Underlying stock
        self.underlying = Stock(self.ticker, 'SMART', 'USD')
        self.ib.qualifyContracts(self.underlying)
        
        # Historical bars for calculating indicators
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
        
        log(f"Momentum strategy initialized for {ticker}")
        log(f"RSI Period: {rsi_period}, Momentum Period: {momentum_period}")
    
    def on_bar_update(self, bars, has_new_bar):
        """Handle new bar updates"""
        if has_new_bar and len(bars) >= max(self.rsi_period, self.momentum_period):
            self.check_signals()
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return None
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_momentum(self, prices, period=10):
        """Calculate momentum (rate of change)"""
        if len(prices) < period:
            return None
            
        current_price = prices[-1]
        past_price = prices[-period]
        momentum = ((current_price - past_price) / past_price) * 100
        return momentum
    
    def check_signals(self):
        """Check for momentum signals"""
        if len(self.bars) < max(self.rsi_period, self.momentum_period):
            return
            
        # Calculate indicators
        closes = [bar.close for bar in self.bars]
        rsi = self.calculate_rsi(closes, self.rsi_period)
        momentum = self.calculate_momentum(closes, self.momentum_period)
        
        if rsi is None or momentum is None:
            return
            
        log(f"Current Price: ${closes[-1]:.2f}, RSI: {rsi:.2f}, Momentum: {momentum:.2f}%")
        
        # Check for entry signals
        if not self.in_trade:
            # Buy when RSI is oversold and momentum is turning positive
            if rsi < self.rsi_oversold and momentum > 0:
                self.buy()
            # Sell short when RSI is overbought and momentum is turning negative
            elif rsi > self.rsi_overbought and momentum < 0:
                log(f"Short signal detected (RSI: {rsi:.2f}, Momentum: {momentum:.2f}%) but shorting not implemented")
        
        # Check for exit signals
        elif self.in_trade:
            # Exit long position when RSI becomes overbought or momentum weakens
            if rsi > self.rsi_overbought or momentum < -2.0:
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
        
        log("Momentum strategy stopped")


# Helper function for logging
def log(message):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
