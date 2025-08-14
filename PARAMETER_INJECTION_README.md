# Parameter Injection System Documentation

## Overview

The Options Trading system automatically injects key parameters into your strategies at runtime, making it easy to create reusable strategies that can work with different ticker symbols, account numbers, and trading modes without modifying the code.

## 🔧 What Gets Injected

### 1. Ticker Symbols (`tickers`)
- **Type**: `List[str]`
- **Source**: Entered in the "Tickers" field in the UI
- **Example**: `['AAPL', 'TSLA', 'SPY']`
- **Usage**: `params.get('tickers', [])`

### 2. Account Numbers (`accounts`)
- **Type**: `List[str]`
- **Source**: Selected from IBKR accounts in the UI
- **Example**: `['DU1234567', 'DU1234568']`
- **Usage**: `params.get('accounts', [])`

### 3. Trading Mode (`paper_trading`)
- **Type**: `bool`
- **Source**: Determined by the IBKR connection type
- **Example**: `True` for paper trading, `False` for live trading
- **Usage**: `params.get('paper_trading', True)`

### 4. Additional Parameters
- **Strategy ID**: `params.get('strategy_id')`
- **Strategy Name**: `params.get('strategy_name')`
- **Connection Type**: `params.get('connection_type')`
- **Deployment ID**: `params.get('deployment_id')`

## 📋 How to Use Injected Parameters

### Basic Strategy Template

```python
from strategies.base import Strategy
import asyncio

class MyStrategy(Strategy):
    name = "My Strategy"
    
    async def run(self, ib, params, log):
        """
        Main strategy execution method
        Parameters are automatically injected by the system
        """
        log(f"Starting {self.name} strategy...")
        
        # Get injected parameters
        tickers = params.get('tickers', [])
        accounts = params.get('accounts', [])
        paper_trading = params.get('paper_trading', True)
        
        log(f"Processing tickers: {tickers}")
        log(f"Processing accounts: {accounts}")
        log(f"Paper trading mode: {paper_trading}")
        
        # Use the parameters in your strategy logic
        for ticker in tickers:
            log(f"Processing ticker: {ticker}")
            # Your trading logic here
            
        for account in accounts:
            log(f"Processing account: {account}")
            # Your account-specific logic here
            
        return True

# Strategy instance - REQUIRED for the system to work
strategy = MyStrategy()
```

### Parameter Access Patterns

```python
# Method 1: Direct access (may raise KeyError if missing)
tickers = params['tickers']
accounts = params['accounts']

# Method 2: Safe access with defaults (recommended)
tickers = params.get('tickers', [])
accounts = params.get('accounts', [])
paper_trading = params.get('paper_trading', True)

# Method 3: Type checking for safety
if isinstance(params.get('tickers'), list):
    tickers = params['tickers']
else:
    log("Warning: No tickers provided")
    tickers = []

# Method 4: Validation with error handling
tickers = params.get('tickers')
if not tickers:
    log("Error: No tickers provided")
    return False
```

## 🚀 Deployment Process

### 1. Set Ticker Symbols
- Enter comma-separated ticker symbols in the "Tickers" field
- Example: `AAPL, TSLA, SPY`
- The system will convert this to: `['AAPL', 'TSLA', 'SPY']`

### 2. Select Accounts
- Connect to IBKR to load available accounts
- Select one or more accounts from the dropdown
- Selected accounts will be injected as a list

### 3. Choose Trading Mode
- Select "Paper" or "Live" trading mode
- The system connects to the appropriate IBKR port
- Paper trading mode is automatically detected and injected

### 4. Deploy Strategy
- Click "Deploy" to execute the strategy
- Parameters are automatically injected at runtime
- Your strategy receives the `params` dictionary with all values

## 🔒 Read-Only Nature

**Important**: Injected parameters cannot be modified in your strategy code. They are:

- **Set by the system** when deploying
- **Read-only** during execution
- **Consistent** across all deployments of the same strategy
- **Validated** before deployment

## 📊 Parameter Summary Display

The UI provides several visual indicators:

1. **Parameter Summary Panel**: Shows current values that will be injected
2. **Parameter Injection Zone**: Displays what gets injected at runtime
3. **Code Highlight**: Shows the exact `params` dictionary that will be passed
4. **Read-Only Indicators**: Clear visual cues that parameters are auto-injected

## 🧪 Testing Parameter Injection

Run the test script to verify the system works:

```bash
python test_parameter_injection.py
```

This will test:
- Parameter loading and injection
- Strategy execution with injected parameters
- Parameter access patterns
- Type validation

## 💡 Best Practices

### 1. Always Use Safe Access
```python
# Good
tickers = params.get('tickers', [])
accounts = params.get('accounts', [])

# Avoid (may crash if parameter missing)
tickers = params['tickers']
```

### 2. Validate Parameters Early
```python
async def run(self, ib, params, log):
    # Validate required parameters
    tickers = params.get('tickers', [])
    if not tickers:
        log("Error: No tickers provided")
        return False
        
    accounts = params.get('accounts', [])
    if not accounts:
        log("Error: No accounts provided")
        return False
```

### 3. Use Descriptive Logging
```python
log(f"Processing {len(tickers)} tickers: {tickers}")
log(f"Processing {len(accounts)} accounts: {accounts}")
log(f"Trading mode: {'Paper' if paper_trading else 'Live'}")
```

### 4. Handle Edge Cases
```python
# Handle empty lists gracefully
if not tickers:
    log("Warning: No tickers to process")
    return True
    
# Handle single vs multiple accounts
if len(accounts) == 1:
    account = accounts[0]
    log(f"Single account mode: {account}")
else:
    log(f"Multi-account mode: {len(accounts)} accounts")
```

## 🔍 Debugging Parameter Issues

### Check Parameter Values
```python
async def run(self, ib, params, log):
    # Debug: Log all parameters
    log(f"All parameters received: {params}")
    
    # Debug: Check specific parameters
    log(f"Tickers type: {type(params.get('tickers'))}")
    log(f"Tickers value: {params.get('tickers')}")
    log(f"Accounts type: {type(params.get('accounts'))}")
    log(f"Accounts value: {params.get('accounts')}")
```

### Verify Parameter Types
```python
# Ensure parameters are the expected types
if not isinstance(params.get('tickers'), list):
    log(f"Error: tickers should be list, got {type(params.get('tickers'))}")
    return False
```

## 📚 Example Strategies

See the following files for complete examples:
- `strategies/examples.py` - Basic strategy examples
- `strategies/risky_options_bot.py` - Advanced strategy with parameter usage
- `test_parameter_injection.py` - Test strategies

## 🆘 Troubleshooting

### Common Issues

1. **"No tickers provided" error**
   - Make sure you've entered ticker symbols in the UI
   - Check that the tickers field is not empty

2. **"No accounts selected" error**
   - Connect to IBKR first
   - Select at least one account from the dropdown

3. **Parameter type errors**
   - Always use `params.get()` with defaults
   - Validate parameter types before use

4. **Missing parameters**
   - Check the parameter summary in the UI
   - Verify all required parameters are set before deployment

### Getting Help

If you encounter issues:
1. Check the parameter summary panel in the UI
2. Review the deployment history for error messages
3. Run the test script to verify system functionality
4. Check the browser console for JavaScript errors

## 🔄 Parameter Updates

Parameters can be updated without modifying strategy code:

- **Tickers**: Edit the tickers field and save
- **Accounts**: Select different accounts in the UI
- **Trading Mode**: Change connection type (paper/live)

The strategy code remains unchanged - only the injected values change.
