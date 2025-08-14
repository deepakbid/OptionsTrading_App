const { useState, useEffect, useMemo } = React;

function cls(...args) { return args.filter(Boolean).join(" "); }




// Bot data
const bots = [
  {
    id: '1',
    icon: '🤖',
    name: 'Broken Wing Iron Fly...',
    chartData: [10, 12, 8, 15, 18, 16, 20, 17, 22, 19, 25, 23, 28, 24, 26],
    totalPL: '$644',
    returnPercent: '+6.4%',
    closedPL: '$644',
    closedPercent: '+6.4%',
    change: '-$56',
    changePercent: '-0.5%',
    position: 1,
    risk: '$49',
    allocation: '$10K',
    winRate: '63%',
    betPercent: '-1.68',
    autos: true
  },
  {
    id: '2',
    icon: '🤖',
    name: 'C-Brok-Opening Ran...',
    chartData: [5, 8, 12, 10, 15, 20, 18, 25, 22, 28, 30, 26, 32, 29, 35],
    totalPL: '$290',
    returnPercent: '+7.3%',
    closedPL: '$410',
    closedPercent: '+10.3%',
    change: '-$120',
    changePercent: '-2.7%',
    position: 2,
    risk: '$2,830',
    allocation: '$4K',
    winRate: '100%',
    betPercent: '166.07',
    autos: true
  },
  {
    id: '3',
    icon: '🤖',
    name: 'C-Brok-Stocks',
    chartData: [20, 18, 22, 25, 23, 28, 26, 30, 28, 32, 35, 33, 38, 36, 40],
    totalPL: '$1,367',
    returnPercent: '+9.1%',
    closedPL: '$2,239',
    closedPercent: '+14.9%',
    change: '-$105',
    changePercent: '-0.6%',
    position: 3,
    risk: '$17.2K',
    allocation: '$15K',
    winRate: '80%',
    betPercent: '31.15',
    autos: true
  },
  {
    id: '4',
    icon: '🤖',
    name: 'C-Brok-Stocks -TQQQ',
    chartData: [15, 17, 14, 16, 19, 17, 21, 18, 22, 20, 24, 22, 25, 23, 26],
    totalPL: '$418',
    returnPercent: '+4.2%',
    closedPL: '$418',
    closedPercent: '+4.2%',
    change: '--',
    changePercent: '--',
    position: '--',
    risk: '--',
    allocation: '$10K',
    winRate: '67%',
    betPercent: '--',
    autos: true
  },
  {
    id: '5',
    icon: '🤖',
    name: 'C-T-IRA-Liquid Equiti...',
    chartData: [8, 12, 10, 15, 13, 18, 16, 21, 19, 24, 22, 27, 25, 30, 28],
    totalPL: '$522',
    returnPercent: '+20.9%',
    closedPL: '$522',
    closedPercent: '+20.9%',
    change: '--',
    changePercent: '--',
    position: '--',
    risk: '--',
    allocation: '$2.5K',
    winRate: '58%',
    betPercent: '--',
    autos: false
  },
  {
    id: '6',
    icon: 'CT',
    name: 'C-T-IRA-Stocks Clone',
    chartData: [12, 10, 14, 11, 16, 13, 18, 15, 20, 17, 22, 19, 24, 21, 25],
    totalPL: '--',
    returnPercent: '--',
    closedPL: '--',
    closedPercent: '--',
    change: '--',
    changePercent: '--',
    position: '--',
    risk: '--',
    allocation: '$50K',
    winRate: '--',
    betPercent: '--',
    autos: false
  }
];

// Simple chart component
function SimpleChart({ data, height = 40 }) {
  if (!data || data.length === 0) return <div className="h-10 bg-gray-100 rounded"></div>;
  
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min;
  
  return (
    <div className="relative h-10 w-full">
      <svg className="w-full h-full" viewBox={`0 0 ${data.length * 4} 40`}>
        <polyline
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          points={data.map((d, i) => `${i * 4},${40 - ((d - min) / range) * 35}`).join(' ')}
          className="text-blue-500"
        />
      </svg>
    </div>
  );
}

function App() {
  const [error, setError] = useState(null);



  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Top bar */}
      <header className="border-b border-gray-200 bg-gray-50/70 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-semibold tracking-tight text-gray-900">IBKR Options Strategies</h1>
          <div className="text-xs text-gray-500">Connected to FastAPI Backend</div>
        </div>
      </header>

      {error && (
        <div className="mx-auto max-w-7xl px-4 py-2">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700">
            <strong>Error:</strong> {error}
            <button onClick={() => setError(null)} className="ml-2 text-red-500 hover:text-red-700">×</button>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-7xl px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sidebar: Navigation */}
        <aside className="lg:col-span-3">
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="px-4 py-3 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-900">Option Alpha</h2>
            </div>
            <nav className="p-4">
              <ul className="space-y-3">
                {['Home', 'Bots', 'Positions', 'Trade Ideas', 'ODTE Oracle', 'ODTE Backtester', 'Screener', 'Community', 'Calendar', 'OA Labs', 'Settings'].map((item) => (
                  <li key={item}>
                    <button
                      className={cls(
                        "w-full text-left px-3 py-2 rounded-lg text-sm transition-colors",
                        item === 'Bots' 
                          ? "bg-blue-50 text-blue-700 font-semibold" 
                          : "text-gray-700 hover:bg-gray-50"
                      )}
                    >
                      {item}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </aside>

        {/* Main panel */}
        <section className="lg:col-span-9 space-y-6">
          {/* Selected strategy header */}
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Bots</h3>
                <p className="text-sm text-gray-500">Manage your trading bots and strategies</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-sm text-white">New Bot</button>
                <select className="px-3 py-2 rounded-xl bg-gray-100 border border-gray-300 text-sm text-gray-700">
                  <option>Library</option>
                  <option>Custom</option>
                  <option>Template</option>
                </select>
              </div>
            </div>
          </div>

          {/* Bots Content */}
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex gap-2 flex-wrap">
              {['Live', 'Paper', 'On', 'Off', 'Position', 'Error'].map(filter => (
                <button
                  key={filter}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white hover:bg-gray-50 transition-colors"
                >
                  {filter}
                </button>
              ))}
            </div>

            {/* Metrics Summary */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-9 gap-3">
              {[
                { label: 'TOTAL P/L', value: '$26,180', highlight: true },
                { label: 'RETURN %', value: '+16.0%', highlight: true },
                { label: 'CLOSED P/L', value: '$28,531', highlight: true },
                { label: 'CLOSED %', value: '+17.4%', highlight: true },
                { label: 'CHANGE', value: '-$901', negative: true },
                { label: 'CHANGE %', value: '-0.6%', negative: true },
                { label: 'RISK', value: '$37,513' },
                { label: 'ALLOCATION', value: '$164,000' },
                { label: 'BETA WEIGHT', value: '25.89' },
              ].map(({ label, value, highlight, negative }) => (
                <div
                  key={label}
                  className={cls(
                    "p-3 border border-gray-200 rounded-lg text-center",
                    highlight ? "bg-green-50 border-green-200" : 
                    negative ? "bg-red-50 border-red-200" : 
                    "bg-white"
                  )}
                >
                  <div className="text-xs font-semibold text-gray-600 mb-1">{label}</div>
                  <div className={cls(
                    "text-sm font-bold",
                    negative ? "text-red-600" : "text-gray-900"
                  )}>{value}</div>
                </div>
              ))}
            </div>

            {/* Bots Table */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-700"></th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Bot</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">30D</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Total P/L</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Return %</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Closed P/L</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Closed %</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Change</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Change %</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Pos</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Risk</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Allocation</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Win Rate</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Beta Weight</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-700">Autos</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {bots.map((bot) => (
                      <tr key={bot.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                            <span className="text-xs font-semibold text-blue-600">{bot.icon}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900">{bot.name}</td>
                        <td className="px-4 py-3">
                          <div className="w-20 h-8 bg-gray-100 rounded border">
                            <SimpleChart data={bot.chartData} height={32} />
                          </div>
                        </td>
                        <td className={cls("px-4 py-3 font-medium", 
                          bot.totalPL?.startsWith('$') && !bot.totalPL?.includes('-') ? 'text-green-600' : 
                          bot.totalPL?.includes('-') ? 'text-red-600' : 'text-gray-900'
                        )}>
                          {bot.totalPL || '--'}
                        </td>
                        <td className={cls("px-4 py-3 font-medium", 
                          bot.returnPercent?.startsWith('+') ? 'text-green-600' : 
                          bot.returnPercent?.startsWith('-') ? 'text-red-600' : 'text-gray-900'
                        )}>
                          {bot.returnPercent || '--'}
                        </td>
                        <td className={cls("px-4 py-3 font-medium", 
                          bot.closedPL?.startsWith('$') && !bot.closedPL?.includes('-') ? 'text-green-600' : 
                          bot.closedPL?.includes('-') ? 'text-red-600' : 'text-gray-900'
                        )}>
                          {bot.closedPL || '--'}
                        </td>
                        <td className={cls("px-4 py-3 font-medium", 
                          bot.closedPercent?.startsWith('+') ? 'text-green-600' : 
                          bot.closedPercent?.startsWith('-') ? 'text-red-600' : 'text-gray-900'
                        )}>
                          {bot.closedPercent || '--'}
                        </td>
                        <td className={cls("px-4 py-3 font-medium", 
                          bot.change?.startsWith('$') && !bot.change?.includes('-') ? 'text-green-600' : 
                          bot.change?.includes('-') ? 'text-red-600' : 'text-gray-900'
                        )}>
                          {bot.change || '--'}
                        </td>
                        <td className={cls("px-4 py-3 font-medium", 
                          bot.changePercent?.startsWith('+') ? 'text-green-600' : 
                          bot.changePercent?.startsWith('-') ? 'text-red-600' : 'text-gray-900'
                        )}>
                          {bot.changePercent || '--'}
                        </td>
                        <td className="px-4 py-3 text-gray-900">{bot.position}</td>
                        <td className="px-4 py-3 text-gray-900">{bot.risk}</td>
                        <td className="px-4 py-3 text-gray-900">{bot.allocation}</td>
                        <td className="px-4 py-3 text-gray-900">{bot.winRate || '--'}</td>
                        <td className="px-4 py-3 text-gray-900">{bot.betPercent || '--'}</td>
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={bot.autos}
                            onChange={(e) => {
                              const updatedBots = bots.map(b => 
                                b.id === bot.id ? { ...b, autos: e.target.checked } : b
                              );
                              // Update bots state if you want to persist changes
                            }}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

        </section>
      </div>


    </div>
  );
}



// Render the app
ReactDOM.render(<App />, document.getElementById('root'));
