import { useEffect, useState } from 'react';
import axios from 'axios';
import { Search, Filter, RefreshCw, AlertTriangle, CheckCircle, Edit, Trash2 } from 'lucide-react';

interface KBStats {
    total_indexed: number;
    categories: Record<string, number>;
    malicious_count: number;
}

interface KBItem {
    id: number;
    fqdn: string;
    category: string;
    is_malicious: boolean;
    confidence: number;
    summary: string;
    vector_status: string;
    crawled_at: string;
    analyzed_at: string;
}

export default function KnowledgeBase() {
    const [stats, setStats] = useState<KBStats | null>(null);
    const [items, itemsSet] = useState<KBItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [categoryFilter, setCategoryFilter] = useState("All");
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [editingItem, setEditingItem] = useState<KBItem | null>(null);
    const [categories, setCategories] = useState<{ id: number, name: string }[]>([]);

    const fetchCategories = async () => {
        try {
            const res = await axios.get('/api/v2/categories/');
            setCategories(res.data);
        } catch (e) {
            console.error(e);
        }
    }

    const fetchStats = async () => {
        try {
            const res = await axios.get('/api/v2/kb/stats');
            setStats(res.data);
        } catch (e) {
            console.error(e);
        }
    }

    const fetchItems = async () => {
        setLoading(true);
        try {
            const res = await axios.get('/api/v2/kb/items', {
                params: {
                    page,
                    limit: 10,
                    search,
                    category: categoryFilter
                }
            });
            itemsSet(res.data.data);
            setTotal(res.data.total);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchStats();
        fetchCategories();
    }, []);

    useEffect(() => {
        fetchItems();
    }, [page, search, categoryFilter]);

    const handleRebuild = async (id: number) => {
        if (!confirm("Force re-index this item?")) return;
        try {
            await axios.post(`/api/v2/kb/items/${id}/rebuild`);
            alert("Re-indexing triggered!");
            fetchItems();
        } catch (e) {
            alert("Failed to rebuild");
        }
    }

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingItem) return;
        try {
            await axios.patch(`/api/v2/kb/items/${editingItem.id}`, {
                category: editingItem.category,
                is_malicious: editingItem.is_malicious,
                summary: editingItem.summary
            });
            alert("Metadata updated and re-indexed!");
            setEditingItem(null);
            fetchItems();
            fetchStats();
        } catch (e) {
            alert("Update failed");
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm("Remove this item from Knowledge Base?")) return;
        try {
            await axios.delete(`/api/v2/kb/items/${id}`);
            fetchItems();
            fetchStats();
        } catch (e) {
            alert("Delete failed");
        }
    }

    return (
        <div className="space-y-6">
            {/* Header Stats */}
            <div className="grid grid-cols-3 gap-6">
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm">Total Indexed</h3>
                    <p className="text-3xl font-bold text-white">{(stats?.total_indexed || 0).toLocaleString()}</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm">Malicious Domains</h3>
                    <p className="text-3xl font-bold text-red-400">{(stats?.malicious_count || 0).toLocaleString()}</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-gray-400 text-sm">Top Category</h3>
                    <p className="text-3xl font-bold text-blue-400">
                        {Object.entries(stats?.categories || {}).sort((a, b) => b[1] - a[1])[0]?.[0] || "-"}
                    </p>
                </div>
            </div>

            {/* Controls */}
            <div className="flex gap-4 mb-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-3 text-gray-400" size={18} />
                    <input
                        type="text"
                        placeholder="Search domains..."
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-blue-500"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <select
                    className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                >
                    <option value="All">All Categories</option>
                    {categories.map(c => (
                        <option key={c.id} value={c.name}>{c.name}</option>
                    ))}
                    {/* Allow filtering by old categories too if they exist in stats? Maybe later */}
                </select>
                <button onClick={fetchItems} className="bg-gray-800 text-white p-2 rounded-lg hover:bg-gray-700">
                    <RefreshCw size={20} />
                </button>
            </div>

            {/* Table */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-900 border-b border-gray-700">
                        <tr>
                            <th className="px-6 py-4 text-xs font-medium text-gray-400 uppercase">Domain</th>
                            <th className="px-6 py-4 text-xs font-medium text-gray-400 uppercase">Category</th>
                            <th className="px-6 py-4 text-xs font-medium text-gray-400 uppercase">Malicious</th>
                            <th className="px-6 py-4 text-xs font-medium text-gray-400 uppercase">Confidence</th>
                            <th className="px-6 py-4 text-xs font-medium text-gray-400 uppercase">Vector Status</th>
                            <th className="px-6 py-4 text-xs font-medium text-gray-400 uppercase text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {loading ? (
                            <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-500">Loading...</td></tr>
                        ) : items.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-750">
                                <td className="px-6 py-4 font-medium text-gray-200">{item.fqdn}</td>
                                <td className="px-6 py-4 text-gray-300">
                                    <span className="bg-gray-700 px-2 py-1 rounded text-xs">{item.category}</span>
                                </td>
                                <td className="px-6 py-4">
                                    {item.is_malicious ? (
                                        <span className="flex items-center gap-1 text-red-400 text-xs bg-red-400/10 px-2 py-1 rounded w-fit">
                                            <AlertTriangle size={12} /> True
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-1 text-green-400 text-xs bg-green-400/10 px-2 py-1 rounded w-fit">
                                            <CheckCircle size={12} /> False
                                        </span>
                                    )}
                                </td>
                                <td className="px-6 py-4 text-gray-300">{(item.confidence * 100).toFixed(0)}%</td>
                                <td className="px-6 py-4">
                                    <span className="text-xs text-blue-300 bg-blue-500/10 px-2 py-1 rounded">Checked</span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => setEditingItem(item)}
                                            className="p-1 text-gray-400 hover:text-white"
                                            title="Edit Metadata"
                                        >
                                            <Edit size={16} />
                                        </button>
                                        <button
                                            onClick={() => handleRebuild(item.id)}
                                            className="p-1 text-gray-400 hover:text-blue-400"
                                            title="Re-Index Vector"
                                        >
                                            <RefreshCw size={16} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(item.id)}
                                            className="p-1 text-gray-400 hover:text-red-400"
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <div className="p-4 border-t border-gray-700 flex justify-between items-center text-sm text-gray-400">
                    <span>Showing {items.length} of {total} items</span>
                    <div className="flex gap-2">
                        <button
                            disabled={page === 1}
                            onClick={() => setPage(p => p - 1)}
                            className="px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <button
                            disabled={items.length < 10}
                            onClick={() => setPage(p => p + 1)}
                            className="px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            {/* Edit Modal */}
            {editingItem && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-4">Edit Metadata: {editingItem.fqdn}</h2>
                        <form onSubmit={handleUpdate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Category</label>
                                <select
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    value={editingItem.category}
                                    onChange={e => setEditingItem({ ...editingItem, category: e.target.value })}
                                >
                                    {/* Include current if not in list */}
                                    {!categories.find(c => c.name === editingItem.category) && (
                                        <option value={editingItem.category}>{editingItem.category} (Current)</option>
                                    )}
                                    {categories.map(c => (
                                        <option key={c.id} value={c.name}>{c.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Malicious Status</label>
                                <select
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white outline-none"
                                    value={editingItem.is_malicious ? "true" : "false"}
                                    onChange={e => setEditingItem({ ...editingItem, is_malicious: e.target.value === "true" })}
                                >
                                    <option value="false">False (Safe)</option>
                                    <option value="true">True (Malicious)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Analysis Summary</label>
                                <textarea
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white h-32 focus:outline-none focus:border-blue-500"
                                    value={editingItem.summary}
                                    onChange={e => setEditingItem({ ...editingItem, summary: e.target.value })}
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setEditingItem(null)}
                                    className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                                >
                                    Save & Re-Index
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
