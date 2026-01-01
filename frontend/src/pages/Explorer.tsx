import { useEffect, useState } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { AlertCircle, CheckCircle, Clock, Search, XCircle, ExternalLink } from 'lucide-react';

// Types
interface CrawlResult {
    url?: string;
    http_status?: number;
    title?: string;
}

interface Item {
    id: number;
    fqdn: string;
    status: string;
    priority: number;
    updated_at: string;
    created_at: string;
    crawl_result?: CrawlResult;
}

export default function Explorer() {
    const [items, setItems] = useState<Item[]>([]);
    const [loading, setLoading] = useState(false);

    // Filters
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [page, setPage] = useState(0);
    const limit = 50;

    const fetchItems = async () => {
        setLoading(true);
        try {
            const params: any = { skip: page * limit, limit };
            if (statusFilter) params.status = statusFilter;
            if (search) params.search = search;

            const res = await axios.get('/api/v2/pipeline/items', { params });
            setItems(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, [page, statusFilter]);

    // Handle Search on Enter or Button
    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(0); // Reset to first page
        fetchItems();
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'COMPLETED': return <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs font-bold border border-green-500/30 flex w-fit items-center gap-1"><CheckCircle size={12} /> COMPLETED</span>;
            case 'CRAWLED_SUCCESS': return <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs font-bold border border-blue-500/30 flex w-fit items-center gap-1"><CheckCircle size={12} /> CRAWLED</span>;
            case 'CRAWLED_FAIL': return <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 text-xs font-bold border border-red-500/30 flex w-fit items-center gap-1"><XCircle size={12} /> FAILED</span>;
            case 'CRAWLING': return <span className="px-2 py-1 rounded bg-purple-500/20 text-purple-400 text-xs font-bold border border-purple-500/30 flex w-fit items-center gap-1 animate-pulse"><Clock size={12} /> CRAWLING</span>;
            case 'DISCOVERED': return <span className="px-2 py-1 rounded bg-gray-700 text-gray-400 text-xs font-bold border border-gray-600 flex w-fit items-center gap-1"><Clock size={12} /> DISCOVERED</span>;
            default: return <span className="px-2 py-1 rounded bg-gray-800 text-gray-500 text-xs border border-gray-700">{status}</span>;
        }
    };

    return (
        <div>
            {/* Filters Bar */}
            <div className="flex flex-col md:flex-row gap-4 mb-6 bg-gray-800 p-4 rounded-xl border border-gray-700">
                <form onSubmit={handleSearch} className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search FQDN..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-gray-900 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                </form>

                <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
                    className="bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                    <option value="">All Statuses</option>
                    <option value="DISCOVERED">DISCOVERED</option>
                    <option value="CRAWLED_SUCCESS">CRAWLED (SUCCESS)</option>
                    <option value="CRAWLED_FAIL">CRAWLED (FAIL)</option>
                    <option value="COMPLETED">COMPLETED</option>
                </select>

                <button
                    onClick={fetchItems}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
                >
                    Refresh
                </button>
            </div>

            {/* Table */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-900/50 border-b border-gray-700 text-gray-400 text-sm">
                            <th className="p-4 font-medium">FQDN / URL</th>
                            <th className="p-4 font-medium">Status</th>
                            <th className="p-4 font-medium">HTTP Code</th>
                            <th className="p-4 font-medium">Page Title / Info</th>
                            <th className="p-4 font-medium">Last Updated</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {loading ? (
                            <tr><td colSpan={5} className="p-8 text-center text-gray-500">Loading data...</td></tr>
                        ) : items.length === 0 ? (
                            <tr><td colSpan={5} className="p-8 text-center text-gray-500">No items found matching your criteria.</td></tr>
                        ) : (
                            items.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-750 transition-colors text-sm">
                                    <td className="p-4">
                                        <div className="font-medium text-white">{item.fqdn}</div>
                                        {item.crawl_result?.url && item.crawl_result.url !== `https://${item.fqdn}` && (
                                            <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                                <ExternalLink size={10} /> {item.crawl_result.url}
                                            </div>
                                        )}
                                    </td>
                                    <td className="p-4">
                                        {getStatusBadge(item.status)}
                                    </td>
                                    <td className="p-4">
                                        {item.crawl_result?.http_status ? (
                                            <span className={`font-mono ${item.crawl_result.http_status >= 400 ? 'text-red-400' : 'text-green-400'}`}>
                                                {item.crawl_result.http_status}
                                            </span>
                                        ) : (
                                            <span className="text-gray-600">-</span>
                                        )}
                                    </td>
                                    <td className="p-4 max-w-xs truncate text-gray-400" title={item.crawl_result?.title || ''}>
                                        {item.crawl_result?.title || '-'}
                                    </td>
                                    <td className="p-4 text-gray-500">
                                        {item.updated_at ? format(new Date(item.updated_at), 'MMM d, HH:mm:ss') : '-'}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4 px-2">
                <button
                    disabled={page === 0}
                    onClick={() => setPage(p => p - 1)}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-300 disabled:opacity-50 hover:bg-gray-700"
                >
                    Previous
                </button>
                <span className="text-gray-500 text-sm">Page {page + 1}</span>
                <button
                    disabled={items.length < limit}
                    onClick={() => setPage(p => p + 1)}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-300 disabled:opacity-50 hover:bg-gray-700"
                >
                    Next
                </button>
            </div>
        </div>
    );
}
