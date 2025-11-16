import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { DollarSign, Zap, Clock, Shield, BarChart, ChevronDown, Star, Award, TrendingUp, Cpu } from 'lucide-react';

// --- Components ---

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-green-400"></div>
      <div className="absolute text-white">
        <Cpu size={32} />
      </div>
    </div>
  );
}

function ErrorDisplay({ error }) {
  return (
    <div className="flex items-center justify-center h-screen bg-gray-900 text-gray-200">
      <div className="bg-red-900/50 border border-red-500/50 p-8 rounded-2xl shadow-lg text-center max-w-lg mx-auto">
        <h2 className="text-3xl font-bold text-red-300 mb-4">Connection Error</h2>
        <p className="text-lg text-gray-300 mb-2">Failed to fetch data from the MonadPulse API.</p>
        <p className="text-sm text-gray-400 mb-6">Please ensure the backend server is running on `http://localhost:8000`.</p>
        <code className="bg-gray-800 p-2 rounded text-red-400 text-xs break-all">{error.message}</code>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon, trend, positive = true }) {
  const Icon = icon;
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-2xl border border-gray-700/50 shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-400">{title}</span>
        <Icon className="text-gray-500" size={20} />
      </div>
      <div className="text-3xl font-bold text-white mb-2">{value}</div>
      <div className={`text-xs ${positive ? 'text-green-400' : 'text-red-400'}`}>
        {trend}
      </div>
    </div>
  );
}

function ValidatorRow({ rank, name, uptime_pct, apy_pct, mev_efficiency, is_omega_partner }) {
  let rankClass = "text-gray-300";
  if (rank === 1) rankClass = "text-yellow-400 font-bold";
  if (rank === 2) rankClass = "text-gray-300 font-bold";
  if (rank === 3) rankClass = "text-yellow-600 font-bold";

  return (
    <tr className={`border-b border-gray-800/50 hover:bg-gray-800/40 ${is_omega_partner ? 'bg-green-900/30' : ''}`}>
      <td className="p-4 text-center">
        <span className={`flex items-center justify-center ${rankClass}`}>
          {rank === 1 && <Award size={16} className="mr-2" />}
          {rank}
        </span>
      </td>
      <td className="p-4 font-medium text-white">{name} {is_omega_partner && <Star size={14} className="inline-block ml-1 text-yellow-400" />}</td>
      <td className="p-4 text-green-400">{uptime_pct.toFixed(2)}%</td>
      <td className="p-4 text-green-400">{apy_pct.toFixed(2)}%</td>
      <td className="p-4 text-white font-mono text-right">${mev_efficiency.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
    </tr>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-900/80 backdrop-blur-md p-4 rounded-lg border border-gray-700 shadow-xl">
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-lg font-bold text-white">
          {payload[0].value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
        </p>
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
          throw new Error('Failed to fetch data from API');
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

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 font-sans p-4 md:p-8">
      {/* Header */}
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-3">
          <Cpu size={32} className="text-green-400" />
          <h1 className="text-3xl font-bold text-white">MonadPulse</h1>
          <span className="bg-green-500/20 text-green-300 text-xs font-medium px-3 py-1 rounded-full border border-green-400/30">
            Mainnet Live
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-400">Last Updated: {lastUpdated.toLocaleTimeString()}</span>
          <button className="flex items-center space-x-2 bg-gray-800/50 px-4 py-2 rounded-lg border border-gray-700/50 hover:bg-gray-800">
            <span className="text-sm">Network: Monad Mainnet</span>
            <ChevronDown size={16} />
          </button>
        </div>
      </header>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Total MEV Captured (14d)"
          value={kpi ? `$${(kpi.total_mev / 1000000).toFixed(2)}M` : 'Loading...'}
          icon={DollarSign}
          trend={kpi ? `+${kpi.mev_change_pct.toFixed(1)}% vs last period` : '...'}
          positive={kpi ? kpi.mev_change_pct >= 0 : true}
        />
        <KPICard
          title="Network TPS (24h Avg)"
          value={kpi ? kpi.network_tps.toLocaleString() : 'Loading...'}
          icon={Zap}
          trend="Stable"
          positive={true}
        />
        <KPICard
          title="Top Validator by MEV"
          value={kpi ? kpi.top_validator : 'Loading...'}
          icon={Award}
          trend={kpi && kpi.top_validator_is_partner ? "Powered by Omega Engine" : "Unoptimized"}
          positive={kpi ? kpi.top_validator_is_partner : false}
        />
        <KPICard
          title="Avg. MEV Efficiency"
          value={kpi ? `${kpi.avg_mev_efficiency.toFixed(1)}%` : 'Loading...'}
          icon={TrendingUp}
          trend="Network Average"
          positive={true}
        />
      </div>

      {/* Main Content Area: Chart + Validator List */}
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Left Column: Chart */}
        <div className="lg:w-2/3 w-full">
          <div className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-2xl border border-gray-700/50 shadow-lg h-[500px]">
            <h2 className="text-xl font-semibold text-white mb-4">Network-Wide MEV (USD) - Last 14 Days</h2>
            <ResponsiveContainer width="100%" height="90%">
              <AreaChart
                data={chart}
                margin={{ top: 10, right: 30, left: 20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorMev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" fontSize={12} />
                <YAxis
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickFormatter={(value) => `$${value / 1000}k`}
                  domain={['dataMin - 50000', 'dataMax + 50000']}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="MEV Captured (USD)"
                  stroke="#10B981"
                  fillOpacity={1}
                  fill="url(#colorMev)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Column: Validator Leaderboard */}
        <div className="lg:w-1/3 w-full">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 shadow-lg h-[500px] flex flex-col">
            <div className="p-6 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white">Genesis Validator Leaderboard</h2>
              <p className="text-sm text-gray-400">Ranked by MEV Efficiency</p>
            </div>
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-gray-800/80 backdrop-blur-md">
                  <tr>
                    <th className="p-4 text-center">Rank</th>
                    <th className="p-4">Validator</th>
                    <th className="p-4">Uptime</th>
                    <th className="p-4">APY</th>
                    <th className="p-4 text-right">MEV (24h)</th>
                  </tr>
                </thead>
                <tbody>
                  {validators.map(v => (
                    <ValidatorRow key={v.rank} {...v} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
