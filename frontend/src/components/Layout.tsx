import { Archive, BarChart2, Globe, Search, Settings, ShieldAlert, Activity, Bot, Database, Rss } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export default function Layout({ children }: { children: React.ReactNode }) {
    const location = useLocation();

    const menuItems = [
        { name: 'Dashboard', path: '/', icon: BarChart2 },
        { name: 'Intel Explorer', path: '/explorer', icon: Globe },
        { name: 'Knowledge Base', path: '/kb', icon: Database },
        { name: 'Pipeline Monitor', path: '/pipeline', icon: Activity },
        { name: 'Policies', path: '/policies', icon: ShieldAlert },
        { name: 'Feed Sources', path: '/feeds', icon: Rss },
        { name: 'Categories', path: '/categories', icon: Archive },
        { name: 'AI Analyst', path: '/chat', icon: Bot },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];

    return (
        <div className="min-h-screen bg-gray-950 text-white flex">
            {/* Sidebar */}
            <aside className="w-64 bg-gray-900 border-r border-gray-800 flex-shrink-0">
                <div className="p-6">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                        W-Intel v2.0
                    </h1>
                    <p className="text-xs text-gray-500 mt-1">Autonomous Threat Intelligence</p>
                </div>

                <nav className="mt-4 px-3">
                    {menuItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${isActive
                                    ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }`}
                            >
                                <item.icon size={18} />
                                {item.name}
                            </Link>
                        )
                    })}
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <header className="h-16 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm flex items-center justify-between px-8 sticky top-0 z-10">
                    <h2 className="text-lg font-semibold text-gray-200">
                        {menuItems.find(i => i.path === location.pathname)?.name || 'W-Intel'}
                    </h2>
                    <div className="flex items-center gap-4">
                        <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                        <span className="text-xs text-gray-400 font-mono">SYSTEM ONLINE</span>
                    </div>
                </header>

                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
