#!/usr/bin/env python3
"""
Database seeding script for Options Trading application.
Adds sample strategies to the database.
"""
import sys
import os
from sqlmodel import create_engine, Session, select
from app.models import StrategyModel

# Use synchronous PostgreSQL connection for seeding
DB_URL = "postgresql://postgres:password@localhost:5432/options_trading"

# Sample strategies data
SAMPLE_STRATEGIES = [
    {
        "name": "Iron Butterfly",
        "description": "A neutral options strategy that profits from low volatility. Involves selling an ATM call and put while buying OTM call and put wings.",
        "code": """
class IronButterfly(Strategy):
    name = "Iron Butterfly Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        mid_strike = float(params.get("mid_strike"))
        width = int(params.get("width", 25))
        qty = int(params.get("qty", 1))
        
        log(f"Creating Iron Butterfly: {symbol} {expiry} {mid_strike}±{width}")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Iron Butterfly strategy completed!")
        """
    },
    {
        "name": "Short Put Spread",
        "description": "A bullish strategy that involves selling a put at a higher strike and buying a put at a lower strike.",
        "code": """
class ShortPutSpread(Strategy):
    name = "Short Put Spread Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        short_strike = float(params["short_strike"])
        long_strike = float(params["long_strike"])
        qty = int(params.get("qty", 1))
        
        log(f"Creating Short Put Spread: {symbol} {expiry} {short_strike}/{long_strike}")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Short Put Spread strategy completed!")
        """
    },
    {
        "name": "Long Call",
        "description": "A simple bullish strategy that profits from upward price movement in the underlying asset.",
        "code": """
class LongCall(Strategy):
    name = "Long Call Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        strike = float(params["strike"])
        qty = int(params.get("qty", 1))
        
        log(f"Buying {qty} {symbol} {expiry} {strike} Call")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Long Call strategy completed!")
        """
    },
    {
        "name": "Covered Call",
        "description": "A strategy that involves owning the underlying asset and selling call options against it.",
        "code": """
class CoveredCall(Strategy):
    name = "Covered Call Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        strike = float(params["strike"])
        qty = int(params.get("qty", 100))
        
        log(f"Creating Covered Call: {symbol} {expiry} {strike} x {qty}")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Covered Call strategy completed!")
        """
    },
    {
        "name": "Straddle",
        "description": "A neutral strategy that profits from significant price movement in either direction.",
        "code": """
class Straddle(Strategy):
    name = "Straddle Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        strike = float(params["strike"])
        qty = int(params.get("qty", 1))
        
        log(f"Creating Straddle: {symbol} {expiry} {strike} x {qty}")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Straddle strategy completed!")
        """
    },
    {
        "name": "Calendar Spread",
        "description": "A strategy that involves buying and selling options with different expiration dates.",
        "code": """
class CalendarSpread(Strategy):
    name = "Calendar Spread Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        short_expiry = params.get("short_expiry")
        long_expiry = params.get("long_expiry")
        strike = float(params["strike"])
        qty = int(params.get("qty", 1))
        
        log(f"Creating Calendar Spread: {symbol} {short_expiry}/{long_expiry} {strike}")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Calendar Spread strategy completed!")
        """
    },
    {
        "name": "Butterfly Spread",
        "description": "A limited risk, limited reward strategy that profits from the underlying asset staying near a specific price.",
        "code": """
class ButterflySpread(Strategy):
    name = "Butterfly Spread Strategy"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        lower_strike = float(params["lower_strike"])
        middle_strike = float(params["middle_strike"])
        upper_strike = float(params["upper_strike"])
        qty = int(params.get("qty", 1))
        
        log(f"Creating Butterfly Spread: {symbol} {expiry} {lower_strike}/{middle_strike}/{upper_strike}")
        
        # Strategy implementation would go here
        await asyncio.sleep(2)
        log("Butterfly Spread strategy completed!")
        """
    },
    {
        "name": "Hello World",
        "description": "A simple test strategy for demonstration purposes.",
        "code": """
class HelloWorld(Strategy):
    name = "Hello World Strategy"
    
    async def run(self, ib, params, log):
        log("Hello from the strategy!")
        log(f"Received parameters: {params}")
        
        # Simulate some work
        await asyncio.sleep(2)
        log("Strategy completed successfully!")
        """
    }
]

def seed_database():
    """Seed the database with sample strategies."""
    print("🌱 Seeding database with sample strategies...")
    
    # Create engine
    engine = create_engine(DB_URL, echo=False)
    
    with Session(engine) as session:
        # Check if strategies already exist
        existing_strategies = session.exec(select(StrategyModel)).all()
        
        if existing_strategies:
            print(f"⚠️  Found {len(existing_strategies)} existing strategies in database")
            response = input("Do you want to add more strategies? (y/n): ").lower().strip()
            if response != 'y':
                print("Seeding cancelled.")
                return
        
        # Add sample strategies
        added_count = 0
        for strategy_data in SAMPLE_STRATEGIES:
            # Check if strategy already exists
            existing = session.exec(
                select(StrategyModel).where(StrategyModel.name == strategy_data["name"])
            ).first()
            
            if existing:
                print(f"⏭️  Strategy '{strategy_data['name']}' already exists, skipping...")
                continue
            
            # Create new strategy
            strategy = StrategyModel(
                name=strategy_data["name"],
                description=strategy_data["description"],
                code=strategy_data["code"]
            )
            
            session.add(strategy)
            added_count += 1
            print(f"✅ Added strategy: {strategy_data['name']}")
        
        # Commit changes
        session.commit()
        print(f"\n🎉 Successfully added {added_count} new strategies to the database!")
        
        # Show all strategies
        all_strategies = session.exec(select(StrategyModel)).all()
        print(f"\n📊 Total strategies in database: {len(all_strategies)}")
        for strategy in all_strategies:
            print(f"  - {strategy.name}")

def main():
    """Main function."""
    try:
        seed_database()
    except KeyboardInterrupt:
        print("\n❌ Seeding cancelled by user.")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
