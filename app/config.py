import os
from dotenv import load_dotenv

load_dotenv()

def env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

# IBKR Connection Settings
# FIXED: Correct port assignments for TWS
# Standard TWS Ports:
# - 7496: Live Trading (TWS) 
# - 7497: Paper Trading (TWS)
# Standard IB Gateway Ports:
# - 4001: Live Trading (Gateway)
# - 4002: Paper Trading (Gateway)

IB_HOST = env("IB_HOST", "127.0.0.1")
IB_PAPER_PORT = int(env("IB_PAPER_PORT", "7497"))  # Paper trading port (TWS)
IB_LIVE_PORT = int(env("IB_LIVE_PORT", "7496"))    # Live trading port (TWS)
IB_PAPER_CLIENT_ID = int(env("IB_PAPER_CLIENT_ID", "1101"))  # Unique per environment/process
IB_LIVE_CLIENT_ID = int(env("IB_LIVE_CLIENT_ID", "1201"))    # Unique per environment/process
ACCOUNT = env("ACCOUNT", "")
USE_PAPER = env("USE_PAPER", "1") == "1"

# Database Settings
DB_HOST = env("DB_HOST", "localhost")
DB_PORT = int(env("DB_PORT", "5432"))
DB_NAME = env("DB_NAME", "options_trading")
DB_USER = env("DB_USER", "postgres")
DB_PASSWORD = env("DB_PASSWORD", "password")

# Construct database URL
DB_URL = env("DB_URL", f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Add validation to warn about potential misconfigurations
def validate_ib_config():
    """Validate IBKR configuration and warn about potential issues."""
    warnings = []
    
    # Check if ports are the same
    if IB_PAPER_PORT == IB_LIVE_PORT:
        warnings.append(f"⚠️  Paper and Live ports are the same ({IB_PAPER_PORT}). This will cause connection issues!")
    
    # Check for common port misconfigurations
    if IB_PAPER_PORT == 7496:
        warnings.append(f"⚠️  Paper port is set to 7496, which is typically the LIVE trading port for TWS!")
    
    if IB_LIVE_PORT == 7497:
        warnings.append(f"⚠️  Live port is set to 7497, which is typically the PAPER trading port for TWS!")
    
    # Check client IDs
    if IB_PAPER_CLIENT_ID == IB_LIVE_CLIENT_ID:
        warnings.append(f"⚠️  Paper and Live client IDs are the same ({IB_PAPER_CLIENT_ID}). Use different IDs!")
    
    # Print configuration summary
    print("=" * 60)
    print("IBKR Configuration Summary:")
    print("-" * 60)
    print(f"Host: {IB_HOST}")
    print(f"Paper Port: {IB_PAPER_PORT} (Client ID: {IB_PAPER_CLIENT_ID})")
    print(f"Live Port: {IB_LIVE_PORT} (Client ID: {IB_LIVE_CLIENT_ID})")
    print(f"Default Mode: {'Paper' if USE_PAPER else 'Live'} (USE_PAPER={USE_PAPER})")
    
    if warnings:
        print("-" * 60)
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(warning)
    else:
        print("✅ Configuration looks correct!")
    
    print("=" * 60)
    
    return len(warnings) == 0

# Validate on import
if __name__ != "__main__":  # Only validate when imported, not when run directly
    validate_ib_config()
