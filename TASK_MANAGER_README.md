# 🔄 Task Manager Dashboard

The Task Manager Dashboard provides real-time visibility into running strategies and helps users easily identify them in Windows Task Manager. This feature ensures that users can monitor their trading strategies at the system level and quickly identify which processes correspond to which strategies.

## 🎯 Features

### 📊 Real-Time Dashboard
- **Live Statistics**: Shows total running strategies, paper trading count, and live trading count
- **Auto-refresh**: Updates every 5 seconds automatically
- **Manual Refresh**: Manual refresh button for immediate updates

### 🔍 Strategy Identification
- **Process Details**: Shows Process ID (PID) for each running strategy
- **Strategy Information**: Displays strategy name, tickers, accounts, and trading mode
- **Task Manager Tips**: Clear instructions on how to identify strategies in Windows Task Manager

### 🛠️ Management Tools
- **Stop Strategies**: One-click stop button for each running strategy
- **Status Monitoring**: Real-time status updates for all running strategies
- **Deployment Tracking**: Links strategies to their deployment records

## 🖥️ How to Use

### 1. Access the Task Manager Tab
1. Open the Options Trading application
2. Click on the **🔄 Task Manager** tab
3. View the dashboard with real-time information

### 2. Monitor Running Strategies
The dashboard shows:
- **Total Running**: Number of currently active strategies
- **Paper Trading**: Count of strategies running in paper trading mode
- **Live Trading**: Count of strategies running in live trading mode

### 3. View Strategy Details
Each running strategy displays:
- Strategy name and ID
- Ticker symbols being traded
- Account numbers
- Trading mode (Paper/Live)
- Deployment ID
- Process ID (PID)
- Start time
- Task Manager identification information

### 4. Stop Strategies
- Click the **⏹️ Stop Strategy** button for any running strategy
- Confirm the action in the popup dialog
- The strategy will be stopped and removed from the dashboard

## 🔍 Windows Task Manager Integration

### Finding Strategies in Task Manager

1. **Open Task Manager**
   - Press `Ctrl + Shift + Esc`
   - Or right-click the taskbar and select "Task Manager"

2. **Look for Python Processes**
   - In the **Processes** tab, look for `python.exe` or `pythonw.exe`
   - These are the processes running your strategies

3. **Check Process Details**
   - Right-click on a Python process
   - Select "Go to details"
   - In the **Details** tab, you'll see:
     - **Process ID (PID)**: Match this with the PID shown in the dashboard
     - **Command Line**: Shows the full command that started the process
     - **Process Title**: The console title will show strategy details

4. **Match Process IDs**
   - Compare the PID in Task Manager with the PID shown in the dashboard
   - This confirms which process corresponds to which strategy

### Process Title Information
When a strategy is running, the process title will show:
```
Options Strategy: [Strategy Name] (ID: [ID]) | 📝 Paper | Tickers: [TICKERS] | Accounts: [ACCOUNTS] | Deployment: [DEPLOYMENT_ID]
```

Example:
```
Options Strategy: Iron Condor Bot (ID: 5) | 📝 Paper | Tickers: SPY, QQQ | Accounts: DU1234567 | Deployment: 12
```

## 🏗️ Technical Implementation

### Backend Components

#### Task Registry (`app/runner.py`)
- **TaskRegistry Class**: Manages running tasks and their metadata
- **Process Title Setting**: Sets descriptive process titles for Task Manager visibility
- **Task Information**: Stores comprehensive metadata for each running task

#### API Endpoints (`app/routers/strategies.py`)
- **`/api/tasks/running`**: Returns information about all running tasks
- **`/api/tasks/{sid}/info`**: Returns detailed information about a specific task

### Frontend Components

#### React Components
- **Tab Navigation**: Dedicated Task Manager tab
- **Dashboard**: Real-time statistics and task information
- **Task Cards**: Individual cards for each running strategy
- **Auto-refresh**: 5-second interval updates

#### CSS Styling
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, professional appearance
- **Status Indicators**: Clear visual feedback for different states

## 📱 User Interface

### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Task Manager Dashboard                    [Stats Panel] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────────────┐ │
│ │ 🔄 Running Tasks    │ │ 📋 Task Manager Tips           │ │
│ │                     │ │                                 │ │
│ │ [Task Cards]        │ │ 💻 Process Name: python.exe    │ │
│ │                     │ │ 🔍 Command Line: Check Details │ │
│ │                     │ │ 📝 Process Title: Strategy Info│ │
│ │                     │ │ 💾 Memory Usage: Higher Usage  │ │
│ │                     │ │ 🆔 Process ID: Match PID       │ │
│ └─────────────────────┘ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💻 System Information                                  │ │
│ │ Platform: Windows                                       │ │
│ │ Python Process: python.exe                              │ │
│ │ Task Manager: Ctrl+Shift+Esc                            │ │
│ │ Details Tab: Right-click → "Go to details"             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Task Card Structure
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Strategy Name                    🟢 Running            │
├─────────────────────────────────────────────────────────────┤
│ Strategy ID: 5        Tickers: SPY, QQQ                   │
│ Accounts: DU1234567   Trading Mode: 📝 Paper Trading      │
│ Deployment ID: 12     Process ID: 12345                   │
│ Started: 1/1/2024, 10:30:00 AM                           │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Task Manager Identification                            │
│ Process Name: python.exe                                   │
│ Process ID: 12345                                         │
│ Description: [Full strategy description]                   │
├─────────────────────────────────────────────────────────────┤
│                    [⏹️ Stop Strategy]                     │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Run the Test Suite
```bash
python test_task_manager.py
```

This will test:
- Module imports
- Task registry functionality
- Process title setting
- Parameter injection
- Task management operations

### Manual Testing
1. Start the application: `python run.py`
2. Open http://localhost:8000
3. Navigate to the Task Manager tab
4. Deploy a strategy to see it appear in the dashboard
5. Check Windows Task Manager for the descriptive process names

## 🔧 Configuration

### Auto-refresh Interval
The dashboard automatically refreshes every 5 seconds. This can be modified in the `useEffect` hook in `static/index.html`:

```javascript
// Set up interval to refresh running tasks every 5 seconds
const interval = setInterval(loadRunningTasks, 5000);
```

### Process Title Format
The process title format can be customized in `app/runner.py` by modifying the `create_task_manager_description` function:

```python
def create_task_manager_description(strategy_name: str, strategy_id: int, tickers: List[str], 
                                 accounts: List[str], paper_trading: bool, deployment_id: int) -> str:
    # Customize the format here
    trading_mode = "📝 Paper" if paper_trading else "💰 Live"
    ticker_str = ", ".join(tickers) if tickers else "No tickers"
    account_str = ", ".join(accounts) if accounts else "No accounts"
    
    description = f"Options Strategy: {strategy_name} (ID: {strategy_id}) | {trading_mode} | Tickers: {ticker_str} | Accounts: {account_str} | Deployment: {deployment_id}"
    return description
```

## 🚨 Troubleshooting

### Common Issues

#### Strategies Not Appearing in Dashboard
1. **Check Application Status**: Ensure the web application is running
2. **Verify Strategy Deployment**: Confirm strategies are actually deployed and running
3. **Check Console Logs**: Look for error messages in the browser console
4. **API Endpoints**: Verify `/strategies/api/tasks/running` endpoint is accessible

#### Process Titles Not Updating
1. **Windows Permissions**: Some process title changes require elevated privileges
2. **Python Version**: Ensure you're using a compatible Python version
3. **Dependencies**: Install required packages: `pip install pywin32 psutil`

#### Dashboard Not Refreshing
1. **Browser Console**: Check for JavaScript errors
2. **Network Tab**: Verify API calls are successful
3. **Auto-refresh**: Check if the interval is properly set

### Debug Information
Enable debug logging by checking the browser console and application logs. The system provides detailed error messages for most common issues.

## 🔮 Future Enhancements

### Planned Features
- **Process Resource Monitoring**: CPU and memory usage per strategy
- **Performance Metrics**: Execution time and efficiency tracking
- **Alert System**: Notifications for strategy status changes
- **Process Tree View**: Hierarchical view of related processes
- **Cross-Platform Support**: Linux and macOS compatibility

### Customization Options
- **Dashboard Layouts**: User-configurable dashboard arrangements
- **Custom Metrics**: User-defined performance indicators
- **Export Functionality**: Export task information to various formats
- **Integration APIs**: Webhook support for external monitoring tools

## 📚 Related Documentation

- [Parameter Injection System](PARAMETER_INJECTION_README.md)
- [Strategy Deployment Guide](README.md)
- [API Reference](app/routers/strategies.py)
- [Task Runner Implementation](app/runner.py)

## 🤝 Contributing

To contribute to the Task Manager functionality:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Submit a pull request**

### Development Guidelines
- Follow the existing code style
- Add comprehensive error handling
- Include unit tests for new features
- Update documentation for any changes
- Test on multiple platforms when possible

---

**Note**: The Task Manager Dashboard is designed to work primarily on Windows systems. Linux and macOS support is limited but can be extended by modifying the `set_process_title` function in `app/runner.py`.
