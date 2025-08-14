# 🎯 MNQ Futures Trading Strategy
# Last updated: 2025-08-14
# Strategy: Place limit orders and close based on stop loss/take profit
# Contract: MNQ September 2025 (202509)

"""
MNQ Futures Trading Strategy
Implements a simple futures trading strategy for MNQ contracts
"""

from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import asyncio

from ib_async import IB, Future, LimitOrder

# Use your app's Strategy base if present; otherwise shim for standalone.
try:
    from strategies.base import Strategy
except Exception:  # pragma: no cover
    class Strategy:
        name = "BaseStrategy"
        def __init__(self):
            self.params = {}
            self.tickers = []
            self.accounts = []
            self.ticker = None
            self.account = None
            self.contract_size = 1
            self.limit_offset = 0.25
            self.stop_loss_points = 5.0
            self.ib: Optional[IB] = None


class FuturesMNQStrategy(Strategy):
    name = "FuturesMNQ"

    def __init__(self):
        super().__init__()
        self._running: bool = True
        self._in_trade: bool = False
        self._entry_price: Optional[float] = None
        self._entry_time: Optional[datetime] = None

        self._contract: Optional[Future] = None
        self._ticker_stream = None   # Ticker from reqMktData
        self._tick_size: float = 0.25

        # price snapshots
        self._snapshots: List[Dict[str, Any]] = []

    # ------------------------------ Public API ------------------------------

    async def run(self, log=print) -> bool:
        symbol = (self.ticker or "MNQ").upper()
        acct = (self.account or "").strip() or None

        expiry = str(self.params.get("expiry", "202509"))
        use_delayed = bool(self.params.get("use_delayed", False))
        max_runtime_sec = int(self.params.get("max_runtime_sec", 300))
        demo_close_after = int(self.params.get("close_after_sec", 10))
        tp_mult = float(self.params.get("take_profit_mult", 2.0))

        if not self.ib or not self.ib.isConnected():
            log("❌ IB is not connected. (CLI must set strategy.ib before run())")
            return False

        avg_cost_is_price = bool(self.params.get("avg_cost_is_price", True))

        log(f"▶️  {self.name} for {symbol} {expiry} (acct={acct or 'DEFAULT'})")
        log(f"    contract_size={self.contract_size}, stop_loss={self.stop_loss_points}, "
            f"take_profit_mult={tp_mult}, limit_offset={self.params.get('limit_offset', self.limit_offset)}, "
            f"use_delayed={use_delayed}, avg_cost_is_price={avg_cost_is_price}")

        try:
            # 1) Qualify MNQ
            self._contract = await self._resolve_mnq_contract(symbol, expiry, log)
            if not self._contract:
                log("❌ Could not qualify MNQ contract.")
                return False
            log(f"✅ Using contract conId={self._contract.conId}, exchange={self._contract.exchange}, "
                f"tradingClass={getattr(self._contract,'tradingClass',None)}, "
                f"localSymbol={getattr(self._contract,'localSymbol',None)}")

            # 2) minTick
            await self._load_tick_size(log)

            # 3) Market data (strict NBBO)
            if not await self._setup_market_data(log, use_delayed=use_delayed):
                log("❌ Market data setup failed - aborting.")
                return False

            # 4) Check/adopt existing position (and set proper entry price)
            size, avg_cost = await self._existing_position_and_cost(acct, log)
            if size != 0:
                entry = self._convert_avg_cost_to_price(avg_cost, default_mult=getattr(self._contract, "multiplier", "2"),
                                                        enabled=avg_cost_is_price)
                self._in_trade = True
                self._entry_price = entry
                self._entry_time = datetime.now()
                self._record_price("adopted", log)
                side = "LONG" if size > 0 else "SHORT"
                log(f"🤝 Adopted existing position → side={side}, size={size}, entry_price≈{entry}")
            else:
                log("✅ No existing position")

            # 5) If no position → enter with LIMIT BUY
            if not self._in_trade:
                if not await self._place_limit_buy(acct, log):
                    log("❌ Failed to open position.")
                    return False
                else:
                    log("✅ Position opened")

            # 6) Monitor loop
            log("⏱️  Monitoring position...")
            started = datetime.now()
            while self._running and (datetime.now() - started).seconds < max_runtime_sec:
                self._record_price("monitor", log)

                if await self._check_stop_loss(acct, log):
                    log("🛑 Closed by stop loss.")
                    break
                if await self._check_take_profit(acct, tp_mult, log):
                    log("🎯 Closed by take profit.")
                    break

                if self._in_trade and self._entry_time:
                    dur = (datetime.now() - self._entry_time).seconds
                    if dur >= demo_close_after:
                        log(f"⏰ Demo: time-based close after {dur}s")
                        await self._close_position_limit(acct, log)
                        break

                # IMPORTANT: use asyncio.sleep (not IB.sleep) to avoid nested loop errors
                await asyncio.sleep(1.0)

            log("✅ Monitoring complete.")
            return True

        except Exception as e:
            log(f"❌ Strategy error: {e}")
            return False

        finally:
            await self._cleanup(log)

    def stop(self):
        self._running = False
        try:
            if self._ticker_stream:
                # cancel by Ticker if possible; ignore errors if already gone
                try:
                    self.ib.cancelMktData(self._ticker_stream)
                except Exception:
                    # try by contract as a fallback
                    try:
                        self.ib.cancelMktData(self._contract)
                    except Exception:
                        pass
                print("✅ Cancelled market data subscription")
        except Exception as e:
            print(f"⚠️ cancelMktData error: {e}")

    # ------------------------------ Contract ------------------------------

    async def _resolve_mnq_contract(self, symbol: str, expiry: str, log) -> Optional[Future]:
        attempts: List[Future] = []
        attempts.append(Future(symbol=symbol, lastTradeDateOrContractMonth=expiry, exchange="GLOBEX", currency="USD"))
        attempts.append(Future(symbol=symbol, lastTradeDateOrContractMonth=expiry, exchange="CME",    currency="USD"))
        attempts.append(Future(symbol=symbol, lastTradeDateOrContractMonth=expiry, exchange="",       currency="USD"))
        attempts.append(Future(symbol=symbol, lastTradeDateOrContractMonth=expiry, exchange="GLOBEX", currency="USD", tradingClass="MNQ"))
        attempts.append(Future(symbol=symbol, lastTradeDateOrContractMonth=expiry, exchange="CME",    currency="USD", tradingClass="MNQ"))
        ls = self._mnq_local_symbol_from_expiry(symbol, expiry)
        if ls:
            attempts.append(Future(localSymbol=ls, exchange="GLOBEX", currency="USD"))
            attempts.append(Future(localSymbol=ls, exchange="CME",    currency="USD"))

        for idx, c in enumerate(attempts, 1):
            try:
                log(f"🔎 Qualify attempt {idx}: symbol={getattr(c,'symbol',None)}, "
                    f"expiry={getattr(c,'lastTradeDateOrContractMonth',None)}, exchange={c.exchange!r}, "
                    f"tradingClass={getattr(c,'tradingClass',None)}, localSymbol={getattr(c,'localSymbol',None)}")
                q = await self.ib.qualifyContractsAsync(c)
                if q:
                    log(f"✅ Qualified on attempt {idx} → conId={q[0].conId}, exchange={q[0].exchange}, "
                        f"tradingClass={getattr(q[0],'tradingClass',None)}, localSymbol={getattr(q[0],'localSymbol',None)}")
                    return q[0]
                else:
                    log(f"⚠️ Attempt {idx} returned no results.")
            except Exception as e:
                log(f"❌ Attempt {idx} failed: {e}")
        return None

    def _mnq_local_symbol_from_expiry(self, symbol: str, yyyymm: str) -> Optional[str]:
        if len(yyyymm) != 6 or not yyyymm.isdigit():
            return None
        y = int(yyyymm[:4])
        m = int(yyyymm[4:6])
        codes = {1:"F",2:"G",3:"H",4:"J",5:"K",6:"M",7:"N",8:"Q",9:"U",10:"V",11:"X",12:"Z"}
        mc = codes.get(m)
        if not mc:
            return None
        return f"{symbol}{mc}{str(y)[-1]}"

    # ------------------------------ Market Data ------------------------------

    async def _load_tick_size(self, log):
        try:
            cds = await self.ib.reqContractDetailsAsync(self._contract)
            mt = getattr(cds[0], "minTick", None) if cds else None
            if mt:
                self._tick_size = float(mt)
                log(f"ℹ️ minTick={self._tick_size}")
        except Exception as e:
            log(f"⚠️ could not load minTick, using default {self._tick_size}: {e}")

    async def _setup_market_data(self, log, use_delayed: bool) -> bool:
        try:
            try:
                self.ib.reqMarketDataType(1)  # live
                log("📡 Requested LIVE market data")
            except Exception as e:
                log(f"⚠️ Could not set live market data: {e}")

            if use_delayed:
                try:
                    self.ib.reqMarketDataType(3)  # delayed
                    log("↪️ DELAYED market data enabled")
                except Exception as e:
                    log(f"⚠️ Could not set delayed market data: {e}")

            self._ticker_stream = self.ib.reqMktData(self._contract, "", False, False)

            # Wait up to 5s for NBBO
            deadline = datetime.now().timestamp() + 5.0
            while datetime.now().timestamp() < deadline:
                await self.ib.reqTickersAsync(self._contract)
                self._record_price("first_ticks", log)
                if self._has_nbbo(self._ticker_stream):
                    log(f"✅ NBBO: bid={self._ticker_stream.bid} x {getattr(self._ticker_stream,'bidSize',0)}, "
                        f"ask={self._ticker_stream.ask} x {getattr(self._ticker_stream,'askSize',0)}, "
                        f"last={self._ticker_stream.last}")
                    return True
                # IMPORTANT: use asyncio.sleep here
                await asyncio.sleep(0.2)

            log("❌ NBBO not available within timeout (no trading).")
            return False

        except Exception as e:
            log(f"❌ _setup_market_data failed: {e}")
            return False

    def _has_nbbo(self, t) -> bool:
        return (
            getattr(t, "bid", None) is not None and
            getattr(t, "ask", None) is not None and
            getattr(t, "bidSize", 0) and
            getattr(t, "askSize", 0)
        )

    def _round_to_tick(self, px: float) -> float:
        step = float(getattr(self, "_tick_size", 0.25) or 0.25)
        return round(round(px / step) * step, 10)

    def _nbbo(self) -> Tuple[float, float]:
        t = self._ticker_stream
        return float(t.ask), float(t.bid)

    def _record_price(self, label: str, log):
        t = self._ticker_stream
        if not t:
            return
        snap = {
            "ts": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "label": label,
            "bid": getattr(t, "bid", None),
            "ask": getattr(t, "ask", None),
            "last": getattr(t, "last", None),
            "bidSize": getattr(t, "bidSize", None),
            "askSize": getattr(t, "askSize", None),
            "lastSize": getattr(t, "lastSize", None),
        }
        self._snapshots.append(snap)

    # ------------------------------ Positions & Orders ------------------------------

    async def _existing_position_and_cost(self, acct: Optional[str], log) -> Tuple[int, float]:
        """
        Returns (netSize, avgCost) for the target conId/account; 0,0 if none.
        """
        try:
            positions = await self.ib.reqPositionsAsync()
            conid = getattr(self._contract, "conId", None)
            net = 0
            avg_cost = 0.0
            for p in positions:
                if getattr(p.contract, "conId", None) == conid:
                    if not acct or p.account == acct:
                        net += int(p.position)
                        avg_cost = float(p.avgCost or 0.0)
            log(f"ℹ️ Existing position detected: size={net}, avgCost={avg_cost}")
            return net, avg_cost
        except Exception as e:
            log(f"⚠️ reqPositionsAsync error: {e}")
            return 0, 0.0

    def _convert_avg_cost_to_price(self, avg_cost: float, default_mult: Optional[str], enabled: bool) -> float:
        """
        For MNQ, avgCost is typically price * multiplier (multiplier=2).
        If enabled=True (default), we divide by multiplier to recover a price.
        """
        if not enabled:
            return float(avg_cost or 0.0)
        try:
            mult = float(default_mult or "2")
        except Exception:
            mult = 2.0
        if mult <= 0:
            mult = 2.0
        # safeguard: if avg_cost already looks like a price (~23900-26000), just return it
        if 1000.0 < avg_cost < 100000.0 and abs(avg_cost - 24000.0) < abs(avg_cost / mult - 24000.0):
            return avg_cost
        return float(avg_cost) / mult if avg_cost else 0.0

    async def _place_limit_buy(self, acct: Optional[str], log) -> bool:
        t = self._ticker_stream
        if not self._has_nbbo(t):
            log("❌ No NBBO — refusing to place BUY")
            return False

        ask, bid = self._nbbo()
        off = float(self.params.get("limit_offset", self.limit_offset))
        tif = str(self.params.get("tif", "DAY")).upper()
        px = self._round_to_tick(ask + off)

        self._record_price("pre_entry", log)
        log(f"🛒 LIMIT BUY {self.contract_size} @ {px} (ask={ask}, off={off}, TIF={tif})")

        order = LimitOrder(
            action="BUY",
            totalQuantity=int(self.contract_size),
            lmtPrice=px,
            tif=tif,
            account=acct or None,
        )
        trade = self.ib.placeOrder(self._contract, order)
        ok = await self._wait_for_fill(trade, log, timeout=int(self.params.get("limit_timeout", 30)))
        if not ok:
            try:
                self.ib.cancelOrder(trade.order)
                log("⚠️ Cancelled unfilled BUY after timeout")
            except Exception as e:
                log(f"cancel error: {e}")
            return False

        self._in_trade = True
        self._entry_price = float(trade.orderStatus.avgFillPrice or px)
        self._entry_time = datetime.now()
        self._record_price("post_entry_fill", log)
        log(f"✅ BUY filled @ {self._entry_price}")
        return True

    async def _close_position_limit(self, acct: Optional[str], log) -> bool:
        if not self._in_trade:
            log("ℹ️ No open position to close.")
            return True

        t = self._ticker_stream
        if not self._has_nbbo(t):
            log("❌ No NBBO — refusing to submit SELL")
            return False

        ask, bid = self._nbbo()
        off = float(self.params.get("limit_offset", self.limit_offset))
        tif = str(self.params.get("tif", "DAY")).upper()
        px = self._round_to_tick(bid - off)

        self._record_price("pre_exit", log)
        log(f"🚪 LIMIT SELL {self.contract_size} @ {px} (bid={bid}, off={off}, TIF={tif})")

        order = LimitOrder(
            action="SELL",
            totalQuantity=int(self.contract_size),
            lmtPrice=px,
            tif=tif,
            account=acct or None,
        )
        trade = self.ib.placeOrder(self._contract, order)
        ok = await self._wait_for_close_fill(trade, log, timeout=int(self.params.get("limit_timeout", 30)))
        if not ok:
            log("⚠️ Exit not filled within timeout")
            return False

        close_px = float(trade.orderStatus.avgFillPrice or px)
        self._record_price("post_exit_fill", log)

        if self._entry_price is not None:
            pnl = (close_px - self._entry_price) * int(self.contract_size) * 2.0  # MNQ $2/pt
            log(f"📈 P&L: ${pnl:.2f} (entry {self._entry_price} → exit {close_px})")

        self._in_trade = False
        self._entry_price = None
        self._entry_time = None
        log("✅ Position closed.")
        return True

    async def _wait_for_fill(self, trade, log, timeout=30) -> bool:
        start = datetime.now()
        log(f"⏳ Waiting fill (≤{timeout}s)...")
        while (datetime.now() - start).seconds < timeout:
            # IMPORTANT: asyncio.sleep, not IB.sleep
            await asyncio.sleep(0.4)
            status = getattr(trade.orderStatus, "status", "")
            if status == "Filled":
                return True
            if status in ("Cancelled", "ApiCancelled", "Error"):
                log(f"❌ Order failed: status={status} err={getattr(trade.orderStatus, 'errorMessage', '')}")
                return False
        return False

    async def _wait_for_close_fill(self, trade, log, timeout=30) -> bool:
        start = datetime.now()
        log(f"⏳ Waiting close fill (≤{timeout}s)...")
        while (datetime.now() - start).seconds < timeout:
            await asyncio.sleep(0.4)  # IMPORTANT
            status = getattr(trade.orderStatus, "status", "")
            if status == "Filled":
                log(f"✅ Close filled @ {trade.orderStatus.avgFillPrice}")
                return True
            if status in ("Cancelled", "ApiCancelled", "Error"):
                log(f"❌ Close failed: status={status} err={getattr(trade.orderStatus, 'errorMessage', '')}")
                return False
        return False

    async def _check_stop_loss(self, acct: Optional[str], log) -> bool:
        if not (self._in_trade and self._entry_price):
            return False
        t = self._ticker_stream
        if not self._has_nbbo(t):
            return False
        ask, bid = self._nbbo()
        stop = float(self._entry_price) - float(self.stop_loss_points)
        # Long-only logic; if you add shorts, flip logic appropriately.
        if bid <= stop:
            log(f"🛑 Stop loss hit: side=LONG, entry={self._entry_price}, bid={bid}, ask={ask}, stop_level={stop}")
            await self._close_position_limit(acct, log)
            return True
        return False

    async def _check_take_profit(self, acct: Optional[str], tp_mult: float, log) -> bool:
        if not (self._in_trade and self._entry_price):
            return False
        t = self._ticker_stream
        if not self._has_nbbo(t):
            return False
        ask, bid = self._nbbo()
        target = float(self._entry_price) + float(self.stop_loss_points) * float(tp_mult)
        if ask >= target:
            log(f"🎯 Take-profit hit: ask={ask} >= target={target}")
            await self._close_position_limit(acct, log)
            return True
        return False
 
    # ------------------------------ Cleanup & Summary ------------------------------

    async def _cleanup(self, log):
        try:
            if self._ticker_stream:
                try:
                    self.ib.cancelMktData(self._ticker_stream)
                except Exception:
                    try:
                        self.ib.cancelMktData(self._contract)
                    except Exception:
                        pass
                log("🧹 Market data subscription cancelled")

            if self._in_trade:
                log("⚠️ Exiting with an open position - please manage manually or extend auto-close logic.")

            self._print_price_summary(log)

        except Exception as e:
            log(f"⚠️ Cleanup error: {e}")

    def _print_price_summary(self, log):
        if not self._snapshots:
            log("ℹ️ No price snapshots recorded.")
            return
        log("\n===== PRICE SNAPSHOTS (chronological) =====")
        header = f"{'time':>12}  {'label':>12}  {'bid':>10}  {'ask':>10}  {'last':>10}  {'bidSz':>6}  {'askSz':>6}"
        log(header)
        log("-" * len(header))
        for s in self._snapshots:
            def num(x):
                return f"{x:.2f}" if isinstance(x, (int, float)) else "-"
            log(f"{s['ts']:>12}  {s['label']:>12}  "
                f"{num(s['bid']):>10}  {num(s['ask']):>10}  {num(s['last']):>10}  "
                f"{(str(s['bidSize']) if s['bidSize'] is not None else '-'):>6}  "
                f"{(str(s['askSize']) if s['askSize'] is not None else '-'):>6}")
        log("===========================================\n")
