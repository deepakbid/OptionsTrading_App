# RiskyOptionsBot Strategy (ib_async version)
from strategies.base import Strategy
from ib_async import IB, Stock, Option, MarketOrder, util
from ib_async.objects import BarData
from datetime import datetime, timezone, timedelta
import asyncio

class RiskyOptionsBotStrategy(Strategy):
    """
    Risky Options Bot Strategy (ib_async, Interactive Brokers)
    
    Buys 2 DTE calls on 3 consecutive 5-min higher closes
    and exits on the next bar (simple scalp).
    """
    
    name = "RiskyOptionsBot"
    
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
        
        log(f"Tickers: {tickers}")
        log(f"Accounts: {accounts}")
        log(f"Paper Trading: {paper_trading}")
        
        if not accounts:
            log("No accounts provided, cannot run strategy")
            return False
            
        # Use first ticker for now (can be extended to handle multiple)
        ticker = tickers[0].upper()
        account = accounts[0]
        
        log(f"Running strategy on {ticker} for account {account}")
        
        try:
            # Create the bot instance
            bot = RiskyOptionsBot(ib, ticker, account)
            
            # Run for a limited time (e.g., 1 hour) to demonstrate
            log(f"Bot started, running for 1 hour...")
            await asyncio.sleep(3600)  # Run for 1 hour
            
            # Stop the bot
            bot.stop()
            log(f"{self.name} strategy completed successfully!")
            return True
            
        except Exception as e:
            log(f"Error running strategy: {e}")
            return False


class RiskyOptionsBot:
    """
    Risky Options Bot (ib_async, Interactive Brokers)

    Buys 2 DTE calls on 3 consecutive 5-min higher closes
    and exits on the next bar (simple scalp).
    """

    def __init__(self, ib: IB, ticker: str = "SPY", account: str | None = None):
        self.ib = ib
        self.ticker = ticker.upper()
        self.account = account  # if None we'll pick last managed account after connect
        self.in_trade = False
        self.entry_bars_seen = None
        self.options_contract = None
        self.last_underlying_close = None
        self.last_chain_refresh = None
        self.chains = []

        if not self.ib.isConnected():
            print("⚠️ IB is not connected. Connect before constructing the bot.")
        # Underlying
        self.underlying = Stock(self.ticker, 'SMART', 'USD')
        self.ib.qualifyContracts(self.underlying)

        # Initial chains fetch (sync, on the ib thread)
        self.update_options_chains()

        # 5-minute historical bars with realtime updates
        # Note: keepUpToDate=True => bars.updateEvent(bars, hasNewBar)
        self.bars = self.ib.reqHistoricalData(
            self.underlying,
            endDateTime='',
            durationStr='2 D',
            barSizeSetting='5 mins',
            whatToShow='TRADES',
            useRTH=False,
            keepUpToDate=True,
            formatDate=1
        )
        self.bars.updateEvent += self.on_bar_update

        # Exec/fill logging (optional)
        # (ib_async exposes execDetailsEvent just like ib_insync)
        self.ib.execDetailsEvent += self.exec_status

        # choose default account if not provided
        try:
            if not self.account:
                accts = self.ib.managedAccounts()
                if accts:
                    self.account = accts[-1]
        except Exception:
            pass

        print(f"✅ Bot armed on {self.ticker} using account {self.account or '(unset)'}")

    # -------- helpers --------
    def update_options_chains(self):
        try:
            self.chains = self.ib.reqSecDefOptParams(
                self.underlying.symbol, '', self.underlying.secType, self.underlying.conId
            )
            self.last_chain_refresh = datetime.now(timezone.utc)
        except Exception as e:
            print(f"update_options_chains error: {e}")

    def pick_two_dte_call(self, underlying_last: float) -> Option | None:
        """
        Pick a call ~ $5 OTM with ~2 DTE from available chains.
        """
        if not self.chains:
            return None

        # Prefer SMART, else first chain
        chain = next((c for c in self.chains if getattr(c, 'exchange', '') == 'SMART'), self.chains[0])

        # Choose expiration nearest to 2 calendar days from now
        now = datetime.now(timezone.utc).date()
        def parse_exp(s):  # 'YYYYMMDD' -> date
            return datetime.strptime(str(s), "%Y%m%d").date()

        expirations = sorted(parse_exp(e) for e in chain.expirations)
        if not expirations:
            return None

        target = now + timedelta(days=2)
        # pick expiry with smallest |dte-2|
        expiry = min(expirations, key=lambda d: abs((d - target).days))

        # choose strike >= last + 5
        strikes = sorted(chain.strikes)
        target_strike = next((s for s in strikes if s >= underlying_last + 5), None)
        if target_strike is None:
            return None

        exp_str = expiry.strftime("%Y%m%d")
        return Option(
            self.underlying.symbol,
            exp_str,
            float(target_strike),
            'C',
            'SMART',
            tradingClass=getattr(chain, 'tradingClass', self.underlying.symbol)
        )

    # -------- events --------
    def on_bar_update(self, bars, has_new_bar: bool):
        try:
            if not has_new_bar:
                return

            # refresh option chains about hourly (run on ib thread via this callback)
            if not self.last_chain_refresh or (datetime.now(timezone.utc) - self.last_chain_refresh) > timedelta(hours=1):
                self.update_options_chains()

            if len(bars) < 4:  # need at least 3 prior closes + current
                return

            # Grab last three completed bars (ignore the in-progress one if any)
            # ib_async historical-with-updates appends the forming bar at the end.
            # Using the last 3 *closed* bars => take bars[-2], [-3], [-4] closes,
            # then compare [-2] > [-3] > [-4], and act on the *new* forming bar.
            c_minus1 = bars[-2].close
            c_minus2 = bars[-3].close
            c_minus3 = bars[-4].close

            if not self.in_trade:
                if c_minus1 > c_minus2 and c_minus2 > c_minus3:
                    last = c_minus1
                    opt = self.pick_two_dte_call(last)
                    if not opt:
                        return
                    # Qualify and buy 1 contract
                    self.ib.qualifyContracts(opt)
                    self.options_contract = opt

                    buy = MarketOrder('BUY', 1)
                    if self.account:
                        buy.account = self.account
                    trade = self.ib.placeOrder(self.options_contract, buy)
                    self.last_underlying_close = last
                    self.in_trade = True
                    self.entry_bars_seen = len(bars)
                    print(f"▶️ BUY {self.options_contract.localSymbol if hasattr(self.options_contract, 'localSymbol') else self.options_contract} (underlying close {last})")
                    return
            else:
                # Exit on the very next completed bar after entry (simple scalp)
                # When a new bar closes, len(bars) increases by 1
                if self.entry_bars_seen is not None and len(bars) >= self.entry_bars_seen + 1:
                    sell = MarketOrder('SELL', 1)
                    if self.account:
                        sell.account = self.account
                    self.ib.placeOrder(self.options_contract, sell)
                    print("⏹️ SELL (next bar scalp)")
                    self.in_trade = False
                    self.entry_bars_seen = None
                    self.options_contract = None

        except Exception as e:
            print(f"on_bar_update error: {e}")

    def exec_status(self, trade, fill):
        # Simple fill log
        try:
            sym = getattr(trade.contract, "localSymbol", trade.contract.symbol)
            print(f"✔️ Filled {sym}: {fill.execution.shares}@{fill.execution.price}")
        except Exception:
            print("✔️ Filled")

    # Optional: call this to stop cleanly
    def stop(self):
        try:
            if hasattr(self, "bars"):
                self.ib.cancelHistoricalData(self.bars)
                self.bars.updateEvent -= self.on_bar_update
        except Exception:
            pass
        try:
            self.ib.execDetailsEvent -= self.exec_status
        except Exception:
            pass
        print("🛑 Bot stopped.")


# Strategy instance - REQUIRED for the system to work
strategy = RiskyOptionsBotStrategy()
