import { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Trash2, RefreshCw, Rss, Info, CheckCircle, AlertTriangle, Play } from 'lucide-react';

interface Feed {
    id: number;
    name: string;
    url: string;
    source_type: string;
    description: string;
    is_active: boolean;
    fetch_interval_minutes: number;
    last_fetched_at: string;
    total_items_found: number;
    last_status: string;
    last_error: string;
}

export default function FeedManager() {
    const [feeds, setFeeds] = useState<Feed[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);

    // Form State
    const [newName, setNewName] = useState("");
    const [newUrl, setNewUrl] = useState("");
    const [newType, setNewType] = useState("RSS");
    const [newDesc, setNewDesc] = useState("");
    const [newInterval, setNewInterval] = useState(60);

    const fetchFeeds = async () => {
        try {
            const res = await axios.get('/api/v2/feeds/');
            setFeeds(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFeeds();
        const interval = setInterval(fetchFeeds, 5000); // Live update for status
        return () => clearInterval(interval);
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post('/api/v2/feeds/', {
                name: newName,
                url: newUrl,
                source_type: newType,
                description: newDesc,
                fetch_interval_minutes: newInterval
            });
            setShowAdd(false);
            fetchFeeds();
            // Reset
            setNewName(""); setNewUrl(""); setNewDesc("");
        } catch (e) {
            alert("Failed to create feed");
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure?")) return;
        try {
            await axios.delete(`/api/v2/feeds/${id}`);
            fetchFeeds();
        } catch (e) { console.error(e); }
    };

    const handleToggle = async (id: number) => {
        try {
            await axios.put(`/api/v2/feeds/${id}/toggle`);
            fetchFeeds();
        } catch (e) { console.error(e); }
    };

    const handleFetchNow = async (id: number) => {
        try {
            // Optimistic update
            setFeeds(feeds.map(f => f.id === id ? { ...f, last_status: 'fetching' } : f));
            await axios.post(`/api/v2/feeds/${id}/fetch_now`);
            // The polling will pick up the result
        } catch (e) { console.error(e); }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Rss className="text-orange-400" />
                        Collection Source Manager
                    </h2>
                    <p className="text-gray-400 mt-1">Manage Threat Intelligence Feeds and Auto-Collection</p>
                </div>
                <button
                    onClick={() => setShowAdd(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                >
                    <Plus size={18} /> Add Source
                </button>
            </div>

            {/* Add Modal/Form (Inline for simplicity) */}
            {showAdd && (
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 mb-8 animate-in fade-in slide-in-from-top-4">
                    <h3 className="text-lg font-semibold text-white mb-4">Add New Source</h3>
                    <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input className="bg-gray-900 border border-gray-700 rounded p-2 text-white" placeholder="Name (e.g. OpenPhish)" value={newName} onChange={e => setNewName(e.target.value)} required />
                        <input className="bg-gray-900 border border-gray-700 rounded p-2 text-white" placeholder="URL" value={newUrl} onChange={e => setNewUrl(e.target.value)} required />

                        <select className="bg-gray-900 border border-gray-700 rounded p-2 text-white" value={newType} onChange={e => setNewType(e.target.value)}>
                            <option value="RSS">RSS Feed</option>
                            <option value="CSV">CSV (URL in col 1)</option>
                            <option value="TEXT">Text (Line per URL)</option>
                            <option value="JSON">JSON (Advanced)</option>
                        </select>

                        <input className="bg-gray-900 border border-gray-700 rounded p-2 text-white" type="number" placeholder="Interval (min)" value={newInterval} onChange={e => setNewInterval(Number(e.target.value))} />

                        <input className="bg-gray-900 border border-gray-700 rounded p-2 text-white md:col-span-2" placeholder="Description" value={newDesc} onChange={e => setNewDesc(e.target.value)} />

                        <div className="flex gap-2">
                            <button type="submit" className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded">Create</button>
                            <button type="button" onClick={() => setShowAdd(false)} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded">Cancel</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Feeds Table */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full text-left text-sm text-gray-400">
                    <thead className="bg-gray-900 text-gray-200 uppercase text-xs font-semibold">
                        <tr>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4">Source Name</th>
                            <th className="px-6 py-4">Type</th>
                            <th className="px-6 py-4">Found</th>
                            <th className="px-6 py-4">Last Fetched</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {feeds.map((feed) => (
                            <tr key={feed.id} className="hover:bg-gray-750/50">
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        {feed.last_status === 'fetching' ? (
                                            <RefreshCw className="text-blue-400 animate-spin" size={18} />
                                        ) : feed.last_status === 'error' ? (
                                            <AlertTriangle className="text-red-400" size={18} title={feed.last_error} />
                                        ) : (
                                            <CheckCircle className="text-green-400" size={18} />
                                        )}
                                        <span className={`text-xs uppercase font-bold
                                            ${feed.last_status === 'error' ? 'text-red-400' :
                                                feed.last_status === 'fetching' ? 'text-blue-400' : 'text-green-400'}`}>
                                            {feed.last_status}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="text-white font-medium">{feed.name}</div>
                                    <div className="text-xs text-gray-500 truncate max-w-[200px]" title={feed.url}>{feed.url}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                                        {feed.source_type}
                                    </span>
                                </td>
                                <td className="px-6 py-4 font-mono text-white">
                                    {feed.total_items_found.toLocaleString()}
                                </td>
                                <td className="px-6 py-4 text-xs">
                                    {feed.last_fetched_at ? new Date(feed.last_fetched_at).toLocaleString() : 'Never'}
                                </td>
                                <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                                    <button
                                        onClick={() => handleFetchNow(feed.id)}
                                        className="p-2 hover:bg-blue-600/20 text-blue-400 rounded transition-colors"
                                        title="Fetch Now"
                                    >
                                        <Play size={16} />
                                    </button>
                                    <button
                                        onClick={() => handleToggle(feed.id)}
                                        className={`p-2 rounded transition-colors ${feed.is_active ? 'hover:bg-yellow-600/20 text-yellow-400' : 'hover:bg-green-600/20 text-green-400'}`}
                                        title={feed.is_active ? "Disable" : "Enable"}
                                    >
                                        {feed.is_active ? "⏸" : "▶"}
                                    </button>
                                    <button
                                        onClick={() => handleDelete(feed.id)}
                                        className="p-2 hover:bg-red-600/20 text-red-400 rounded transition-colors"
                                        title="Delete"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {feeds.length === 0 && !loading && (
                    <div className="p-8 text-center text-gray-500">
                        No feeds configured. Add one to start collecting data.
                    </div>
                )}
            </div>
        </div>
    );
}
