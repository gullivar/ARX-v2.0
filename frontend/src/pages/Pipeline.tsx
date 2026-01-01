import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Activity, AlertTriangle, ArrowRight, CheckCircle, Database,
    Globe, Server, RefreshCw, Layers, ShieldCheck, HeartPulse,
    Play, Pause, Terminal, Cpu
} from 'lucide-react';

export default function Pipeline() {
    const [activeTab, setActiveTab] = useState<'monitor' | 'health' | 'logs'>('monitor');

    // Data State
    const [stats, setStats] = useState<any>(null);
    const [bottlenecks, setBottlenecks] = useState<any>(null);
    const [health, setHealth] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        // Fetch Stats & Health (Critical)
        try {
            const [s, h] = await Promise.all([
                axios.get('/api/v2/pipeline/stats'),
                axios.get('/api/v2/pipeline/health')
            ]);
            setStats(s.data);
            setHealth(h.data);
        } catch (e) {
            console.error("Failed to fetch critical pipeline data", e);
        }

        // Fetch Bottlenecks (Heavy, verify resilience)
        try {
            const b = await axios.get('/api/v2/pipeline/stats/bottlenecks');
            setBottlenecks(b.data);
        } catch (e) {
            console.warn("Bottleneck fetch failed or timed out", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 3000);
        return () => clearInterval(interval);
    }, []);

    // Helper Components
    const StatusCard = ({ title, count, icon: Icon, color, isStuck, subtext }: any) => (
        <div className={`relative p-6 rounded-xl border ${isStuck ? 'border-red-500 animate-pulse bg-red-900/10' : 'border-gray-700 bg-gray-800'} flex flex-col items-center justify-center min-w-[200px]`}>
            <div className={`p-3 rounded-full mb-3 ${color} bg-opacity-20`}>
                <Icon size={24} className={color.replace('bg-', 'text-')} />
            </div>
            <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
            <p className="text-3xl font-bold text-white mt-1">{(count || 0).toLocaleString()}</p>
            {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
            {isStuck && (
                <div className="absolute top-2 right-2 text-red-500">
                    <AlertTriangle size={16} />
                </div>
            )}
        </div>
    );

    const Arrow = () => (
        <div className="hidden md:flex items-center justify-center px-4 text-gray-600">
            <ArrowRight size={24} />
        </div>
    );

    return (
        <div>
            {/* Header / Control Bar */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Activity className="text-blue-400" />
                        Pipeline Operations Center
                    </h2>
                    <p className="text-gray-400 mt-1">Unified Monitoring & Control System</p>
                </div>

                <div className="flex bg-gray-800 p-1 rounded-lg border border-gray-700">
                    {[
                        { id: 'monitor', label: 'Flow Monitor', icon: Layers },
                        { id: 'health', label: 'System Health', icon: HeartPulse },
                        { id: 'logs', label: 'Live Logs', icon: Terminal },
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all
                                ${activeTab === tab.id
                                    ? 'bg-blue-600 text-white shadow-lg'
                                    : 'text-gray-400 hover:text-white hover:bg-gray-700'}`}
                        >
                            <tab.icon size={16} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                <div className="flex gap-2">
                    <button onClick={fetchData} className="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors">
                        <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Global Status Banner */}
            {health && (
                <div className={`mb-8 p-4 rounded-xl border flex items-center justify-between
                    ${health.status === 'healthy' ? 'bg-green-900/20 border-green-500/30' :
                        health.status === 'degraded' ? 'bg-yellow-900/20 border-yellow-500/30' :
                            'bg-red-900/20 border-red-500/30'}`}>
                    <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full animate-pulse
                            ${health.status === 'healthy' ? 'bg-green-500' :
                                health.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                        <div>
                            <h3 className={`font-bold ${health.status === 'healthy' ? 'text-green-400' :
                                    health.status === 'degraded' ? 'text-yellow-400' : 'text-red-400'
                                }`}>
                                System Status: {health.status.toUpperCase()}
                            </h3>
                            <p className="text-xs text-gray-400">
                                {health.status === 'healthy' ? 'All systems operational. Auto-recovery active.' :
                                    'Attention required. Check System Health tab.'}
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-4 text-xs font-mono text-gray-400">
                        <span>Last Update: {new Date().toLocaleTimeString()}</span>
                    </div>
                </div>
            )}

            {/* TAB CONTENT: MONITOR */}
            {activeTab === 'monitor' && (
                <div className="animate-in fade-in zoom-in-95 duration-200">

                    {/* Pipeline Visualization */}
                    <div className="flex flex-col md:flex-row justify-center items-stretch gap-4 md:gap-0 mb-8 overflow-x-auto pb-4">
                        <StatusCard
                            title="Discovered"
                            count={stats?.by_status['DISCOVERED']}
                            icon={Globe}
                            color="bg-gray-500 text-gray-400"
                            subtext="Pending"
                        />
                        <Arrow />
                        <StatusCard
                            title="Crawling"
                            count={stats?.by_status['CRAWLING']}
                            icon={Server}
                            color="bg-blue-500 text-blue-400"
                            isStuck={bottlenecks?.stuck_crawling_count > 0}
                            subtext="Active Workers"
                        />
                        <Arrow />
                        <StatusCard
                            title="Analyzing (LLM)"
                            count={stats?.by_status['ANALYZING']}
                            icon={Database}
                            color="bg-purple-500 text-purple-400"
                            isStuck={bottlenecks?.stuck_analyzing_count > 0}
                            subtext="Processing"
                        />
                        <Arrow />
                        <StatusCard
                            title="Completed"
                            count={stats?.by_status['COMPLETED']}
                            icon={CheckCircle}
                            color="bg-green-500 text-green-400"
                            subtext="Indexed"
                        />
                    </div>

                    {/* Bottleneck Alerts */}
                    {(bottlenecks?.stuck_crawling_count > 0 || bottlenecks?.stuck_analyzing_count > 0) && (
                        <div className="bg-red-900/10 border border-red-500/30 rounded-xl p-6 mb-8 flex items-start gap-4">
                            <AlertTriangle className="text-red-500 shrink-0 mt-1" />
                            <div>
                                <h3 className="text-red-400 font-bold">Bottlenecks Detected</h3>
                                <p className="text-gray-400 text-sm mt-1">
                                    {bottlenecks.stuck_crawling_count} items stuck in Crawling, {bottlenecks.stuck_analyzing_count} items stuck in Analyzing.
                                    <br />
                                    <span className="text-gray-500 text-xs">Auto-recovery service will attempt to reset these items automatically.</span>
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Detailed Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                            <h4 className="text-gray-400 text-xs uppercase font-bold mb-2">Total Throughput</h4>
                            <p className="text-2xl font-bold text-white">{(stats?.total || 0).toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                            <h4 className="text-gray-400 text-xs uppercase font-bold mb-2">Crawl Failures</h4>
                            <p className="text-2xl font-bold text-red-400">{(stats?.by_status['CRAWLED_FAIL'] || 0).toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                            <h4 className="text-gray-400 text-xs uppercase font-bold mb-2">Analysis Failures</h4>
                            <p className="text-2xl font-bold text-orange-400">{(stats?.by_status['ANALYSIS_FAIL'] || 0).toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                            <h4 className="text-gray-400 text-xs uppercase font-bold mb-2">Blocked / Filtered</h4>
                            <p className="text-2xl font-bold text-gray-500">{(stats?.by_status['BLOCKED'] || 0).toLocaleString()}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB CONTENT: HEALTH */}
            {activeTab === 'health' && health && (
                <div className="animate-in fade-in zoom-in-95 duration-200">
                    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                        <table className="w-full text-left text-sm text-gray-400">
                            <thead className="bg-gray-900 text-gray-200 uppercase text-xs font-semibold">
                                <tr>
                                    <th className="px-6 py-4">Component</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">Details</th>
                                    <th className="px-6 py-4 text-right">Last Check</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {health.components.map((comp: any) => (
                                    <tr key={comp.name} className="hover:bg-gray-750/50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-white flex items-center gap-3">
                                            {comp.name.includes("Monitor") ? <ShieldCheck size={18} className="text-blue-400" /> :
                                                comp.name.includes("LLM") ? <Cpu size={18} className="text-purple-400" /> :
                                                    comp.name.includes("Database") ? <Database size={18} className="text-green-400" /> :
                                                        <Server size={18} className="text-gray-400" />}
                                            {comp.name}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${comp.status === 'operational' ? 'bg-green-500' :
                                                    comp.status === 'down' ? 'bg-red-500' :
                                                        'bg-yellow-500'
                                                    }`}></div>
                                                <span className={`uppercase font-bold text-xs ${comp.status === 'operational' ? 'text-green-400' :
                                                    comp.status === 'down' ? 'text-red-400' :
                                                        'text-yellow-400'
                                                    }`}>{comp.status}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-300 font-mono text-xs">{comp.details}</td>
                                        <td className="px-6 py-4 text-right font-mono text-xs text-gray-500">
                                            {new Date(comp.last_check).toLocaleTimeString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* TAB CONTENT: LOGS */}
            {activeTab === 'logs' && (
                <div className="animate-in fade-in zoom-in-95 duration-200">
                    <div className="bg-gray-900 rounded-xl border border-gray-700 p-4 font-mono text-xs h-[500px] overflow-y-auto">
                        {stats?.recent_logs.map((log: any) => (
                            <div key={log.id} className="flex gap-3 py-2 border-b border-gray-800 hover:bg-gray-800/50 px-2 rounded">
                                <span className="text-gray-500 shrink-0 w-20">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                                <span className={`font-bold shrink-0 w-16 text-center rounded px-1
                                    ${log.level === 'ERROR' ? 'bg-red-900/30 text-red-400' :
                                        log.level === 'WARNING' ? 'bg-yellow-900/30 text-yellow-400' :
                                            'bg-blue-900/30 text-blue-400'}`}>
                                    {log.level}
                                </span>
                                <span className="text-gray-400 shrink-0 w-24">[{log.stage}]</span>
                                <span className="text-gray-300 break-all">
                                    {log.message}
                                </span>
                            </div>
                        ))}
                        {(!stats?.recent_logs || stats.recent_logs.length === 0) && (
                            <div className="text-center text-gray-600 mt-20">No logs available</div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
