import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, Clock, AlertCircle, Database, Signal } from 'lucide-react';

// --- Components ---

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-screen bg-black">
      <div className="flex flex-col items-center space-y-4">
        <div className="animate-pulse">
          <Database size={48} className="text-orange-500" />
        </div>
        <div className="text-gray-400 text-sm font-mono">INITIALIZING MONADPULSE</div>
      </div>
    </div>
  );
}

function ErrorDisplay({ error }) {
  return (
    <div className="flex items-center justify-center h-screen bg-black text-gray-200">
      <div className="bg-red-950 border-l-4 border-red-600 p-8 max-w-2xl">
        <div className="flex items-center space-x-3 mb-4">
          <AlertCircle className="text-red-500" size={24} />
          <h2 className="text-xl font-mono text-red-400">CONNECTION ERROR</h2>
        </div>
        <p className="text-sm text-gray-400 mb-2 font-mono">API endpoint unavailable</p>
        <code className="bg-black p-3 block text-xs text-red-500 font-mono">{error.message}</code>
      </div>
    </div>
  );
}

function MetricCard({ label, value, subtext, available, trend }) {
  return (
    <div className="bg-gray-950 border border-gray-800 p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="text-xs text-gray-500 font-mono uppercase tracking-wider mb-2">{label}</div>
          {available ? (
            <>
              <div className="text-3xl font-mono font-light text-white mb-1">{value}</div>
              {subtext && <div className="text-xs text-gray-600 font-mono">{subtext}</div>}
            </>
          ) : (
            <>
              <div className="text-xl font-mono text-gray-700 mb-1">—</div>
              <div className="text-xs text-orange-600 font-mono uppercase">
                <Signal size={10} className="inline mr-1" />
                AWAITING API
              </div>
            </>
          )}
        </div>
        {trend && available && (
          <div className="flex items-center space-x-1">
            <TrendingUp size={14} className={trend > 0 ? 'text-green-500' : 'text-red-500'} />
            <span className={`text-xs font-mono ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
              {trend > 0 ? '+' : ''}{trend}%
            </span>
          </div>
        )}
      </div>
      <div className="h-px bg-gray-900"></div>
    </div>
  );
}

function ValidatorEmptyState() {
  return (
    <div className="flex items-center justify-center h-full bg-gray-950/50">
      <div className="text-center space-y-4 p-8">
        <Database size={48} className="mx-auto text-gray-700" />
        <div className="text-sm font-mono text-gray-600 uppercase tracking-wider">
          VALIDATOR DATA
        </div>
        <div className="text-xs font-mono text-orange-600 uppercase">
          <Signal size={12} className="inline mr-2" />
          AWAITING MONAD VALIDATOR API
        </div>
        <div className="text-xs text-gray-700 font-mono max-w-md">
          Real validator metrics will populate automatically when Monad publishes official validator APIs
        </div>
      </div>
    </div>
  );
}

function ValidatorRow({ rank, name, uptime_pct, apy_pct, mev_efficiency }) {
  return (
    <tr className="border-b border-gray-900 hover:bg-gray-950/50 transition-colors">
      <td className="p-3 text-center">
        <span className="text-xs font-mono text-gray-500">{String(rank).padStart(2, '0')}</span>
      </td>
      <td className="p-3">
        <span className="text-xs font-mono text-white">{name}</span>
      </td>
      <td className="p-3 text-right">
        <span className="text-xs font-mono text-green-500">{uptime_pct.toFixed(3)}%</span>
      </td>
      <td className="p-3 text-right">
        <span className="text-xs font-mono text-blue-500">{apy_pct.toFixed(2)}%</span>
      </td>
      <td className="p-3 text-right">
        <span className="text-xs font-mono text-white">{mev_efficiency.toFixed(2)}</span>
      </td>
    </tr>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black border border-gray-700 p-3">
        <div className="text-xs text-gray-500 font-mono mb-1">{label}</div>
        <div className="text-sm font-mono text-white">
          ${payload[0].value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>
    );
  }
  return null;
}

// --- Main App Component ---

export default function App() {
  const [kpi, setKpi] = useState(null);
  const [chart, setChart] = useState([]);
  const [validators, setValidators] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [error, setError] = useState(null);

  const API_BASE_URL = 'http://localhost:8000';

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [kpiRes, chartRes, validatorsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/stats/kpi`),
          fetch(`${API_BASE_URL}/stats/chart`),
          fetch(`${API_BASE_URL}/validators/leaderboard`)
        ]);

        if (!kpiRes.ok || !chartRes.ok || !validatorsRes.ok) {
          throw new Error('API_CONNECTION_FAILED');
        }

        setKpi(await kpiRes.json());
        setChart(await chartRes.json());
        setValidators(await validatorsRes.json());
        setLastUpdated(new Date());
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
        setError(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);

    return () => clearInterval(interval);
  }, []);

  if (error) {
    return <ErrorDisplay error={error} />;
  }

  if (isLoading && !kpi) {
    return <LoadingSpinner />;
  }

  // Determine what data is available
  const hasMEVData = kpi && kpi.total_mev > 0;
  const hasValidatorData = validators && validators.length > 0;
  const hasTPS = kpi && kpi.network_tps > 0;

  return (
    <div className="min-h-screen bg-black text-gray-200 font-sans">
      {/* Top Bar */}
      <div className="bg-gray-950 border-b border-gray-900 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3">
              <Activity size={20} className="text-orange-500" />
              <span className="text-sm font-mono font-semibold text-white tracking-tight">MONADPULSE</span>
            </div>
            <div className="h-4 w-px bg-gray-800"></div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-xs font-mono text-gray-500">MAINNET LIVE</span>
            </div>
          </div>
          <div className="flex items-center space-x-6 text-xs font-mono">
            <div className="flex items-center space-x-2">
              <Clock size={14} className="text-gray-600" />
              <span className="text-gray-600">LAST UPDATE</span>
              <span className="text-gray-400">{lastUpdated.toLocaleTimeString('en-US', { hour12: false })}</span>
            </div>
            <div className="h-4 w-px bg-gray-800"></div>
            <div className="text-gray-600">
              CHAIN: <span className="text-gray-400">MONAD-143</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6 space-y-6">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="NETWORK TPS"
            value={hasTPS ? kpi.network_tps.toLocaleString() : '—'}
            subtext={hasTPS ? 'REAL-TIME FROM MONAD RPC' : null}
            available={hasTPS}
            trend={null}
          />
          <MetricCard
            label="TOTAL MEV (14D)"
            value={hasMEVData ? `$${(kpi.total_mev / 1000000).toFixed(2)}M` : '—'}
            subtext={hasMEVData ? 'CAPTURED VALUE' : null}
            available={hasMEVData}
            trend={kpi && kpi.mev_change_pct > 0 ? kpi.mev_change_pct.toFixed(1) : null}
          />
          <MetricCard
            label="TOP VALIDATOR"
            value={hasValidatorData && kpi.top_validator ? kpi.top_validator : '—'}
            subtext={hasValidatorData ? 'BY MEV EFFICIENCY' : null}
            available={hasValidatorData && kpi.top_validator}
            trend={null}
          />
          <MetricCard
            label="AVG MEV EFFICIENCY"
            value={hasMEVData ? `${kpi.avg_mev_efficiency.toFixed(1)}%` : '—'}
            subtext={hasMEVData ? 'NETWORK AVERAGE' : null}
            available={hasMEVData}
            trend={null}
          />
        </div>

        {/* Chart and Validator Table */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* MEV Trend Chart */}
          <div className="lg:col-span-2 bg-gray-950 border border-gray-900">
            <div className="border-b border-gray-900 p-4">
              <div className="text-xs font-mono text-gray-500 uppercase tracking-wider">MEV CAPTURE TREND</div>
              <div className="text-xs font-mono text-gray-700 mt-1">14 DAY ROLLING WINDOW</div>
            </div>
            <div className="p-6" style={{ height: '400px' }}>
              {chart && chart.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chart} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                    <XAxis
                      dataKey="name"
                      stroke="#4b5563"
                      fontSize={10}
                      fontFamily="monospace"
                      tick={{ fill: '#6b7280' }}
                    />
                    <YAxis
                      stroke="#4b5563"
                      fontSize={10}
                      fontFamily="monospace"
                      tick={{ fill: '#6b7280' }}
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="MEV Captured (USD)"
                      stroke="#f97316"
                      strokeWidth={2}
                      dot={{ fill: '#f97316', r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center space-y-2">
                    <Database size={32} className="mx-auto text-gray-800" />
                    <div className="text-xs font-mono text-gray-700">NO CHART DATA</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Validator Leaderboard */}
          <div className="bg-gray-950 border border-gray-900 flex flex-col" style={{ height: '510px' }}>
            <div className="border-b border-gray-900 p-4">
              <div className="text-xs font-mono text-gray-500 uppercase tracking-wider">VALIDATOR LEADERBOARD</div>
              <div className="text-xs font-mono text-gray-700 mt-1">RANKED BY MEV EFFICIENCY</div>
            </div>
            <div className="flex-1 overflow-hidden">
              {hasValidatorData ? (
                <div className="overflow-y-auto h-full">
                  <table className="w-full text-left">
                    <thead className="sticky top-0 bg-gray-950 border-b border-gray-900">
                      <tr>
                        <th className="p-3 text-center text-xs font-mono text-gray-600 uppercase">RK</th>
                        <th className="p-3 text-xs font-mono text-gray-600 uppercase">VALIDATOR</th>
                        <th className="p-3 text-right text-xs font-mono text-gray-600 uppercase">UPTIME</th>
                        <th className="p-3 text-right text-xs font-mono text-gray-600 uppercase">APY</th>
                        <th className="p-3 text-right text-xs font-mono text-gray-600 uppercase">MEV</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validators.map(v => (
                        <ValidatorRow key={v.rank} {...v} />
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <ValidatorEmptyState />
              )}
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="bg-gray-950 border border-gray-900 p-4">
          <div className="flex items-start justify-between text-xs font-mono">
            <div className="space-y-1">
              <div className="text-gray-600 uppercase tracking-wider">DATA STATUS</div>
              <div className="flex items-center space-x-4 mt-2">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${hasTPS ? 'bg-green-500' : 'bg-gray-700'}`}></div>
                  <span className={hasTPS ? 'text-gray-400' : 'text-gray-700'}>BLOCKCHAIN RPC</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${hasValidatorData ? 'bg-green-500' : 'bg-orange-600'}`}></div>
                  <span className={hasValidatorData ? 'text-gray-400' : 'text-orange-600'}>VALIDATOR API</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${hasMEVData ? 'bg-green-500' : 'bg-orange-600'}`}></div>
                  <span className={hasMEVData ? 'text-gray-400' : 'text-orange-600'}>MEV METRICS</span>
                </div>
              </div>
            </div>
            <div className="text-gray-700 text-right">
              <div>MONADPULSE ANALYTICS v1.0</div>
              <div className="text-gray-800 mt-1">REAL-TIME VALIDATOR INTELLIGENCE</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
