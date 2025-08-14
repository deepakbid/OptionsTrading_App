"""
Example strategies using ib_insync via the adapter.
"""
import asyncio
from strategies.base import Strategy
from ib_insync import Option, MarketOrder, ComboLeg, Contract
from app.ib_adapter import qualify, place_order, wait_for_completion, create_option_contract, create_combo_contract, create_combo_leg

class ExampleIronFly(Strategy):
    name = "Example: Iron Butterfly (ib_insync demo)"

    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")  # e.g. "2025-08-08"
        mid = float(params.get("mid_strike"))
        width = int(params.get("width", 25))
        qty = int(params.get("qty", 1))

        log(f"Creating Iron Butterfly: {symbol} {expiry} {mid}±{width}")

        # Create option contracts
        call = create_option_contract(symbol, expiry, mid, "C")
        put = create_option_contract(symbol, expiry, mid, "P")
        cwing = create_option_contract(symbol, expiry, mid + width, "C")
        pwing = create_option_contract(symbol, expiry, mid - width, "P")

        # Qualify contracts
        log("Qualifying contracts...")
        await qualify(ib, call, put, cwing, pwing)

        # Build combo legs
        legs = [
            create_combo_leg(call, -1, "SELL"),
            create_combo_leg(put, -1, "SELL"),
            create_combo_leg(cwing, 1, "BUY"),
            create_combo_leg(pwing, 1, "BUY")
        ]

        # Create combo contract
        combo = create_combo_contract(symbol, legs)

        # Place order
        order = MarketOrder("SELL", qty)
        trade = await place_order(ib, combo, order)
        log(f"Submitted {qty}x Iron Fly {symbol} {expiry} {mid}±{width}")

        # Wait for completion
        status = await wait_for_completion(ib, trade)
        log(f"Final status: {status}")


class ShortPutSpread(Strategy):
    name = "Short Put Spread (ib_insync)"

    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")  # "2025-08-08"
        short_strike = float(params["short_strike"])
        long_strike = float(params["long_strike"])
        qty = int(params.get("qty", 1))

        log(f"Creating Short Put Spread: {symbol} {expiry} {short_strike}/{long_strike}")

        # Create option contracts
        short_put = create_option_contract(symbol, expiry, short_strike, "P")
        long_put = create_option_contract(symbol, expiry, long_strike, "P")

        # Qualify contracts
        log("Qualifying contracts...")
        await qualify(ib, short_put, long_put)

        # Build combo legs
        legs = [
            create_combo_leg(short_put, -1, "SELL"),
            create_combo_leg(long_put, 1, "BUY")
        ]

        # Create combo contract
        combo = create_combo_contract(symbol, legs)

        # Place order
        order = MarketOrder("SELL", qty)
        trade = await place_order(ib, combo, order)
        log(f"Submitted {qty}x Short Put Spread {symbol} {expiry} {short_strike}/{long_strike}")

        # Wait for completion
        status = await wait_for_completion(ib, trade)
        log(f"Final status: {status}")


class SimpleCallBuy(Strategy):
    name = "Simple Call Buy (ib_insync)"

    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")  # "2025-08-08"
        strike = float(params["strike"])
        qty = int(params.get("qty", 1))

        log(f"Buying {qty} {symbol} {expiry} {strike} Call")

        # Create option contract
        call = create_option_contract(symbol, expiry, strike, "C")

        # Qualify contract
        log("Qualifying contract...")
        await qualify(ib, call)

        # Place order
        order = MarketOrder("BUY", qty)
        trade = await place_order(ib, call, order)
        log(f"Submitted {qty}x {symbol} {expiry} {strike} Call")

        # Wait for completion
        status = await wait_for_completion(ib, trade)
        log(f"Final status: {status}")

class HelloWorld(Strategy):
    name = "Hello World Strategy"

    async def run(self, ib, params, log):
        log("Hello from the strategy!")
        log(f"Received parameters: {params}")
        
        # Simulate some work
        await asyncio.sleep(2)
        log("Strategy completed successfully!")
