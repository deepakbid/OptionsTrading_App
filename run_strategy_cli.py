#!/usr/bin/env python3
"""
Command-line interface to run strategies directly.

Usage:
  python run_strategy_cli.py <strategy_file> [options]

Examples:
  python run_strategy_cli.py cursorstrategies/futures_mnq_strategy.py \
    --tickers MNQ --accounts U2211406 --real-trading --client-id 7 \
    --params expiry=202509,limit_offset=0.25,stop_loss_points=5.0,take_profit_mult=2.0,use_delayed=false,tif=DAY,limit_timeout=30

Diagnostics:
  # Sanity-check event loop + async IB calls:
  python run_strategy_cli.py any.py --diag-loop --real-trading

  # Trace nested run_until_complete calls to locate culprits:
  python run_strategy_cli.py cursorstrategies/futures_mnq_strategy.py --trace-loop --real-trading
"""
import sys
import os
import asyncio
import argparse
import traceback
from typing import Dict, Any

# Ensure app/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))


def enable_loop_tracing():
    """
    Monkey-patch to print a stack trace whenever someone calls
    loop.run_until_complete(...). Helps locate nested-loop offenders.
    """
    import asyncio as _aio
    import traceback as _tb

    orig = _aio.AbstractEventLoop.run_until_complete

    def spy(self, fut):
        print("⚠ run_until_complete called. This is likely your nested-loop culprit.")
        print("---- Stack (most recent call last) ----")
        print("".join(_tb.format_stack(limit=30)))
        print("---------------------------------------")
        return orig(self, fut)

    _aio.AbstractEventLoop.run_until_complete = spy


def parse_parameters(param_string: str) -> Dict[str, Any]:
    """Parse parameter string in format key1=value1,key2=value2"""
    params: Dict[str, Any] = {}
    if not param_string:
        return params
    for item in param_string.split(','):
        item = item.strip()
        if not item:
            continue
        if '=' in item:
            key, value = item.split('=', 1)
            key = key.strip()
            value = value.strip()
            # Try to convert to bool/int/float
            try:
                low = value.lower()
                if low in ('true', 'false'):
                    params[key] = (low == 'true')
                else:
                    if '.' in value:
                        params[key] = float(value)
                    else:
                        params[key] = int(value)
            except Exception:
                params[key] = value
        else:
            # flag without value → True
            params[item] = True
    return params


async def run_strategy_from_file(
    strategy_file: str,
    strategy_filename: str,
    params: Dict[str, Any],
    trace_loop: bool = False,
    client_id: int = 19,
):
    """Run a strategy from a file with the given parameters."""
    try:
        from file_strategy_loader import file_strategy_loader
        from connection_manager import connection_manager

        if trace_loop:
            enable_loop_tracing()

        print(f"🚀 Loading strategy from: {strategy_file}")

        # Load the strategy class from file
        strategy_class = file_strategy_loader.load_strategy_from_file(strategy_filename)
        if not strategy_class:
            print(f"❌ Failed to load strategy from {strategy_file}")
            return False

        print(f"✅ Strategy loaded: {strategy_class.name}")

        # Start connection manager (NO loop juggling here)
        print("🔌 Starting connection manager...")
        await connection_manager.start()

        # Determine connection type
        paper_trading = params.get('paper_trading', True)
        connection_type = "paper" if paper_trading else "real"

        print(f"🔗 Connecting to {connection_type} trading (client_id={client_id})...")

        # Ensure connection (async)
        ok = await connection_manager.ensure_connection(connection_type, client_id=client_id)
        if not ok:
            print(f"❌ Failed to establish {connection_type} trading connection")
            return False

        print(f"✅ Connected to {connection_type} trading successfully!")

        # Get shared IB instance
        from ib_adapter import IBManager
        ib = IBManager.instance().ib

        # Loop-safe logger
        def log(msg: str):
            try:
                ts = asyncio.get_running_loop().time()
            except RuntimeError:
                ts = 0.0
            print(f"[{ts:.2f}] {msg}")

        # Run the strategy
        try:
            log("🎯 Starting strategy execution...")
            log(f"📊 Parameters: {params}")

            # Create strategy instance
            strategy = strategy_class()

            # Wire params & connection
            strategy.params = params
            strategy.ib = ib
            strategy.tickers = params.get('tickers', [])
            strategy.accounts = params.get('accounts', [])
            strategy.ticker = strategy.tickers[0] if strategy.tickers else 'UNKNOWN'
            strategy.account = strategy.accounts[0] if strategy.accounts else 'UNKNOWN'
            strategy.contract_size = params.get('contract_size', 1)
            strategy.limit_offset = params.get('limit_offset', 0.25)
            strategy.stop_loss_points = params.get('stop_loss_points', 5.0)

            # Ensure we are on a running loop
            try:
                _ = asyncio.get_running_loop()
            except RuntimeError:
                log("❌ No running event loop.")
                return False

            # Execute
            result = await strategy.run(log)

            if result:
                log("✅ Strategy completed successfully!")
            else:
                log("❌ Strategy failed!")

            return result

        except Exception as e:
            log(f"❌ Error running strategy: {e}")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Error running strategy: {e}")
        traceback.print_exc()
        return False
    finally:
        # Cleanup connection manager
        try:
            await connection_manager.stop()
            print("🔌 Connection manager stopped")
        except Exception:
            pass


async def main():
    parser = argparse.ArgumentParser(description='Run a trading strategy from command line')

    parser.add_argument('strategy_file', help='Strategy file to run (e.g., cursorstrategies/futures_mnq_strategy.py)')
    parser.add_argument('--tickers', default='MNQ', help='Comma-separated list of tickers')
    parser.add_argument('--accounts', default='', help='Comma-separated list of account numbers')

    # Mutually exclusive: paper vs real
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--paper-trading', action='store_true', help='Use paper trading')
    group.add_argument('--real-trading', action='store_true', help='Use real trading')
    parser.set_defaults(paper_trading=True)  # default to paper if neither provided

    parser.add_argument('--params', default='', help='Additional parameters in key1=value1,key2=value2 format')

    # Diagnostics
    parser.add_argument('--diag-loop', action='store_true',
                        help='Run an async loop/IB sanity check and exit')
    parser.add_argument('--trace-loop', action='store_true',
                        help='Trace nested run_until_complete calls to locate the culprit')

    parser.add_argument('--client-id', type=int, default=19,
                        help='IBKR API client ID to use (default: 19)')

    args = parser.parse_args()

    # Quick diagnostic path (no strategy needed)
    if args.diag_loop:
        from connection_manager import connection_manager
        from ib_adapter import IBManager

        await connection_manager.start()
        mode = "real" if args.real_trading else "paper"
        ok = await connection_manager.ensure_connection(mode, client_id=args.client_id)
        if not ok:
            print("❌ diag: connection failed")
            sys.exit(1)

        ib = IBManager.instance().ib
        loop = asyncio.get_running_loop()
        print(f"diag: loop_id={id(loop)} connected={ib.isConnected()}")

        # Use async IB APIs + asyncio sleep only
        try:
            for i in range(3):
                ct = await ib.reqCurrentTimeAsync()
                print(f"diag[{i}] currentTime={ct}")
                await asyncio.sleep(0.3)
            await connection_manager.stop()
            print("✅ diag: async calls succeeded on one loop")
            sys.exit(0)
        except Exception as e:
            print(f"❌ diag error: {e}")
            await connection_manager.stop()
            sys.exit(1)

    # Normal path: run a strategy file
    if not os.path.exists(args.strategy_file):
        print(f"❌ Strategy file not found: {args.strategy_file}")
        try:
            from file_strategy_loader import file_strategy_loader
            print("Available strategies:")
            for s in file_strategy_loader.get_strategy_files():
                print(f"  - {s}")
        except Exception:
            pass
        return

    # Build params
    strategy_filename = os.path.basename(args.strategy_file)
    params: Dict[str, Any] = {
        'tickers': [t.strip() for t in args.tickers.split(',') if t.strip()],
        'accounts': [a.strip() for a in args.accounts.split(',') if a.strip()],
        'paper_trading': args.paper_trading and not args.real_trading,
        'strategy_name': os.path.splitext(strategy_filename)[0],
    }
    custom_params = parse_parameters(args.params)
    params.update(custom_params)

    # Summary
    print("🎯 Strategy Runner CLI")
    print("=" * 50)
    print(f"Strategy: {args.strategy_file}")
    print(f"Tickers: {params.get('tickers', [])}")
    print(f"Accounts: {params.get('accounts', [])}")
    print(f"Trading Mode: {'Paper' if params.get('paper_trading', True) else 'Real'}")
    print(f"Custom Params: {custom_params}")
    print("=" * 50)

    # Run
    success = await run_strategy_from_file(
        args.strategy_file,
        strategy_filename,
        params,
        trace_loop=args.trace_loop,
        client_id=args.client_id,
    )

    if success:
        print("✅ Strategy completed successfully!")
        sys.exit(0)
    else:
        print("❌ Strategy failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Windows: prefer selector policy for better asyncio/ib_async behavior
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Strategy execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
