import { useEffect, useState } from 'react';
import axios from 'axios';

// Interfaces (Should be in types/index.ts eventually)
interface PipelineItem {
    id: number;
    fqdn: string;
    status: string;
    updated_at: string;
}

interface PipelineLog {
    id: number;
    item_id?: number;
    stage: string;
    level: string;
    message: string;
    timestamp: string;
}

interface Stats {
    total: number;
    by_status: Record<string, number>;
    recent_items: PipelineItem[];
    recent_logs: PipelineLog[];
}

interface ComponentStatus {
    name: string;
    status: string;
    details: string;
    last_check: string;
}

interface SystemHealth {
    status: string;
    components: ComponentStatus[];
}

export default function Dashboard() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [health, setHealth] = useState<SystemHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, healthRes] = await Promise.all([
                    axios.get('/api/v2/pipeline/stats'),
                    axios.get('/api/v2/pipeline/health')
                ]);
                setStats(statsRes.data);
                setHealth(healthRes.data);
                setError(null);
            } catch (err: any) {
                console.error("Failed to fetch dashboard data", err);
                setError(err.message || "Failed to fetch");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, []);

    if (loading && !stats) return <div className="p-8 text-gray-400">Loading Dashboard...</div>;

    return (
        <div>
            {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg mb-6">
                    Error loading stats: {error}
                </div>
            )}

            {/* System Status Summary */}
            {health && (
                <div className="flex gap-4 mb-6">
                    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-red-500 animate-pulse'}`}></div>
                        <span className="text-gray-300 text-sm font-medium">System Status: {health.status.toUpperCase()}</span>
                    </div>
                    {health.components.map((comp) => (
                        <div key={comp.name} className="bg-gray-800 border border-gray-700 rounded-lg p-3 flex items-center gap-3" title={comp.details}>
                            <div className={`w-2 h-2 rounded-full ${comp.status === 'operational' ? 'bg-green-500' : comp.status === 'down' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
                            <span className="text-gray-400 text-xs">{comp.name}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
                {/* 1. Total Items */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Total Items</h3>
                    <p className="text-xs text-gray-500 mb-2">Discovered + Crawled + Completed</p>
                    <p className="text-4xl font-bold text-white">{(stats?.total || 0).toLocaleString()}</p>
                </div>

                {/* 2. Discovered */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Discovered</h3>
                    <p className="text-xs text-gray-500 mb-2">Need to Crawl</p>
                    <p className="text-4xl font-bold text-yellow-400">
                        {(stats?.by_status['DISCOVERED'] || 0).toLocaleString()}
                    </p>
                </div>

                {/* 3. Crawled Success */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Crawled (Success)</h3>
                    <p className="text-xs text-gray-500 mb-2">Content Collected</p>
                    <p className="text-4xl font-bold text-blue-400">
                        {(stats?.by_status['CRAWLED_SUCCESS'] || 0).toLocaleString()}
                    </p>
                </div>

                {/* 4. Crawled Fail */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Failed / Dead</h3>
                    <p className="text-xs text-gray-500 mb-2">40x, 50x, Timeout</p>
                    <p className="text-4xl font-bold text-red-400">
                        {(stats?.by_status['CRAWLED_FAIL'] || 0).toLocaleString()}
                    </p>
                </div>

                {/* 5. Completed (KB) */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Completed (KB)</h3>
                    <p className="text-xs text-gray-500 mb-2">Analyzed & Indexed</p>
                    <p className="text-4xl font-bold text-green-400">
                        {(stats?.by_status['COMPLETED'] || 0).toLocaleString()}
                    </p>
                    {/* Active Analysis Indicator */}
                    {(stats?.by_status['ANALYZING'] || 0) > 0 && (
                        <div className="mt-2 text-xs text-green-300 animate-pulse">
                            ⚡ {(stats?.by_status['ANALYZING'] || 0)} Analyzing...
                        </div>
                    )}
                </div>
            </div>

            {/* Recent Activity Split */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

                {/* Recent Items Table */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Recent Items (Last 10)</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-gray-400">
                            <thead className="text-xs uppercase bg-gray-700/50 text-gray-300">
                                <tr>
                                    <th className="px-3 py-2 rounded-l">Time</th>
                                    <th className="px-3 py-2">Status</th>
                                    <th className="px-3 py-2 rounded-r">FQDN</th>
                                </tr>
                            </thead>
                            <tbody>
                                {stats?.recent_items.map((item) => (
                                    <tr key={item.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                        <td className="px-3 py-2 whitespace-nowrap">
                                            {new Date(item.updated_at).toLocaleTimeString()}
                                        </td>
                                        <td className="px-3 py-2">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium 
                                                ${item.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                                                    item.status === 'ANALYZING' ? 'bg-purple-500/10 text-purple-400' :
                                                        item.status.includes('FAIL') ? 'bg-red-500/10 text-red-400' :
                                                            'bg-gray-700 text-gray-300'}`}>
                                                {item.status}
                                            </span>
                                        </td>
                                        <td className="px-3 py-2 font-mono text-xs text-white truncate max-w-[150px]" title={item.fqdn}>
                                            {item.fqdn}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* System Logs */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">System Logs (Live)</h3>
                    <div className="space-y-2 max-h-[300px] overflow-y-auto font-mono text-xs">
                        {stats?.recent_logs.map((log) => (
                            <div key={log.id} className="flex gap-2 p-2 rounded bg-gray-900/50 border border-gray-700/50">
                                <span className="text-gray-500 shrink-0">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                                <span className={`font-bold shrink-0 w-16 
                                    ${log.level === 'ERROR' ? 'text-red-400' :
                                        log.level === 'WARNING' ? 'text-yellow-400' :
                                            'text-blue-400'}`}>
                                    [{log.level}]
                                </span>
                                <span className="text-gray-300 break-all">
                                    {log.message}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

            </div>

            {/* DEBUG INFO */}
            <div className="bg-gray-900 border border-gray-700 p-4 rounded text-xs font-mono overflow-auto">
                <h4 className="text-gray-400 mb-2">Debug Data:</h4>
                <pre className="text-green-400">{JSON.stringify(stats, null, 2)}</pre>
            </div>
        </div>
    )
}
