# Options Strategy Web App

A Python web application for creating, editing, and running options strategies that execute through IBKR TWS using `ib_insync`.

## Features

- **Strategy Management**: Add, list, edit, and delete strategies
- **Real-time Execution**: Run strategies with JSON parameters and view live logs
- **IBKR Integration**: Execute strategies through Interactive Brokers TWS/Gateway
- **Paper vs Real Trading**: Choose between paper and real trading accounts
- **Modern UI**: React-based frontend with Tailwind CSS
- **Async Task Management**: Background execution with task cancellation
- **Strategy Validation**: Code validation before execution

## Tech Stack

- **Backend**: FastAPI + SQLModel (PostgreSQL, async)
- **Frontend**: React.js + Tailwind CSS
- **IBKR Client**: ib_insync
- **Database**: PostgreSQL with async support
- **Task Runner**: asyncio for background strategy execution

## Prerequisites

1. **Interactive Brokers TWS or IB Gateway**
   - Enable API connections in TWS/Gateway
   - Configure API settings (Sockets)
   - Paper trading port: 7497, Live trading port: 7496

2. **Python 3.8+**
   - Required for async/await support

3. **PostgreSQL 12+**
   - Install PostgreSQL server
   - Create a database user and database

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd options-webapp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**
   ```bash
   # Install PostgreSQL (if not already installed)
   # Windows: Download from https://www.postgresql.org/download/windows/
   # macOS: brew install postgresql
   # Ubuntu: sudo apt-get install postgresql postgresql-contrib
   
   # Start PostgreSQL service
   # Windows: PostgreSQL service should start automatically
   # macOS: brew services start postgresql
   # Ubuntu: sudo systemctl start postgresql
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your IBKR and PostgreSQL settings
   ```

5. **Set up database**
   ```bash
   # Run the database setup script
   python setup_postgres.py
   ```

6. **Environment Variables**
   ```bash
   # IBKR Connection Settings
   IB_HOST=127.0.0.1
   IB_PORT=7497
   IB_CLIENT_ID=999
   ACCOUNT=DU1234567
   USE_PAPER=1
   
   # PostgreSQL Database Settings
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=options_trading
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   ```

## Usage

### Starting the Application

```bash
# Run the FastAPI application
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Accessing the Web Interface

1. Open your browser to `http://localhost:8000`
2. Navigate to the Strategies page
3. Create your first strategy or use the examples

### Creating a Strategy

1. **Navigate to Strategies page**
2. **Fill in the form**:
   - **Name**: Strategy name (e.g., "Iron Butterfly")
   - **Description**: Optional description
   - **Code**: Python code implementing the strategy

3. **Example Strategy Code**:
   ```python
   from strategies.base import Strategy
   from ib_insync import Option, MarketOrder
   from app.ib_adapter import qualify, place_order, wait_for_completion

   class MyStrategy(Strategy):
       name = "My Strategy"
       
       async def run(self, ib, params, log):
           log("Starting strategy...")
           symbol = params.get("symbol", "SPX")
           expiry = params.get("expiry")
           strike = float(params.get("strike"))
           qty = int(params.get("qty", 1))
           
           # Create option contract
           call = Option(symbol, expiry, strike, "C", "SMART")
           
           # Qualify contract
           await qualify(ib, call)
           
           # Place order
           order = MarketOrder("BUY", qty)
           trade = await place_order(ib, call, order)
           
           log(f"Submitted {qty}x {symbol} {expiry} {strike} Call")
           
           # Wait for completion
           status = await wait_for_completion(ib, trade)
           log(f"Final status: {status}")
   ```

### Running a Strategy

1. **Navigate to strategy details**
2. **Enter parameters** (JSON format):
   ```json
   {
     "symbol": "SPX",
     "expiry": "2025-08-08",
     "strike": 5000,
     "qty": 1
   }
   ```
3. **Click "Run Strategy"**
4. **Monitor logs** in real-time

### Running a Strategy from CLI

The project also includes a standalone script, `run_strategy_cli.py`, for executing
strategies directly from the command line. The script connects to Interactive
Brokers using a configurable **client ID**. Use the `--client-id` option to
specify a unique identifier when running multiple IBKR sessions:

```bash
python run_strategy_cli.py cursorstrategies/futures_mnq_strategy.py \
    --tickers MNQ --accounts U2211406 --real-trading --client-id 7
```

If omitted, the client ID defaults to `19`.

## Strategy Examples

### Iron Butterfly
```python
class IronButterfly(Strategy):
    name = "Iron Butterfly"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        mid = float(params.get("mid_strike"))
        width = int(params.get("width", 25))
        qty = int(params.get("qty", 1))
        
        # Create option contracts
        call = Option(symbol, expiry, mid, "C", "SMART")
        put = Option(symbol, expiry, mid, "P", "SMART")
        cwing = Option(symbol, expiry, mid + width, "C", "SMART")
        pwing = Option(symbol, expiry, mid - width, "P", "SMART")
        
        # Qualify contracts
        await qualify(ib, call, put, cwing, pwing)
        
        # Build combo and place order
        # ... (see examples.py for full implementation)
```

### Short Put Spread
```python
class ShortPutSpread(Strategy):
    name = "Short Put Spread"
    
    async def run(self, ib, params, log):
        symbol = params.get("symbol", "SPX")
        expiry = params.get("expiry")
        short_strike = float(params["short_strike"])
        long_strike = float(params["long_strike"])
        qty = int(params.get("qty", 1))
        
        # Create option contracts
        short_leg = Option(symbol, expiry, short_strike, "P", "SMART")
        long_leg = Option(symbol, expiry, long_strike, "P", "SMART")
        
        # Qualify contracts
        await qualify(ib, short_leg, long_leg)
        
        # Build combo and place order
        # ... (see examples.py for full implementation)
```

## API Endpoints

- `GET /` - Main page
- `GET /strategies/` - List strategies
- `POST /strategies/create` - Create new strategy
- `GET /strategies/detail/{id}` - Strategy details
- `POST /strategies/run/{id}` - Run strategy
- `GET /strategies/stop/{id}` - Stop strategy
- `GET /strategies/delete/{id}` - Delete strategy
- `GET /strategies/logs/{id}` - Get strategy logs
- `GET /health` - Health check

## Security Considerations

⚠️ **Important**: This application executes user-provided Python code using `exec()`. 

- **Single-user application**: Designed for personal use
- **No authentication**: Runs in trusted environment
- **Code validation**: Basic validation before execution
- **Sandboxed execution**: Limited builtins available

**For production use**:
- Add authentication and authorization
- Implement proper code sandboxing
- Add rate limiting and resource constraints
- Use secure deployment practices

## Troubleshooting

### Connection Issues
- Ensure TWS/Gateway is running and API is enabled
- Check port numbers (7497 for paper, 7496 for live)
- Verify firewall settings
- Check IBKR account permissions

### Strategy Execution Issues
- Validate strategy code syntax
- Check parameter format (JSON)
- Review IBKR error messages in logs
- Ensure sufficient margin/account permissions

### Common Errors
- `Connection refused`: TWS not running or wrong port
- `Invalid contract`: Contract specification error
- `Insufficient funds`: Account margin issues
- `Order rejected`: Trading permissions or market hours

## Development

### Project Structure
```
options-webapp/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── db.py                # Database setup
│   ├── models.py            # SQLModel models
│   ├── ib_adapter.py        # IBKR adapter
│   ├── strategy_loader.py   # Strategy loading
│   ├── runner.py            # Task runner
│   └── routers/
│       └── strategies.py    # Strategy routes
├── strategies/
│   ├── base.py              # Strategy base class
│   └── examples.py          # Example strategies
├── templates/
│   ├── base.html            # Base template
│   ├── index.html           # Main page
│   └── strategy_detail.html # Strategy details
├── static/
│   └── style.css            # Dark theme CSS
├── requirements.txt         # Dependencies
├── env.example              # Environment template
└── README.md               # This file
```

### Adding New Features
1. **New Strategy Types**: Extend `Strategy` base class
2. **UI Enhancements**: Modify Jinja2 templates
3. **API Endpoints**: Add routes in `routers/`
4. **Database Models**: Add models in `models.py`

## License

This project is for educational purposes. Use at your own risk.

## Disclaimer

Trading involves substantial risk of loss and is not suitable for all investors. This software is provided as-is without any warranties. Always test strategies in paper trading before using real money.
