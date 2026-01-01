import { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Trash, Shield, ShieldAlert, CheckCircle } from 'lucide-react';
import { format } from 'date-fns';

export default function Policies() {
    const [policies, setPolicies] = useState<any[]>([]);
    const [newPattern, setNewPattern] = useState('');
    const [newType, setNewType] = useState('BLACKLIST');

    const fetchPolicies = async () => {
        try {
            const res = await axios.get('/api/v2/policies');
            setPolicies(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchPolicies();
    }, []);

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post('/api/v2/policies', {
                pattern: newPattern,
                type: newType,
                description: 'Added via UI'
            });
            setNewPattern('');
            fetchPolicies();
        } catch (e) {
            alert('Failed to add policy');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure?')) return;
        try {
            await axios.delete(`/api/v2/policies/${id}`);
            fetchPolicies();
        } catch (e) {
            alert('Failed to delete');
        }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                    <Shield className="text-blue-400" />
                    Policy Manager
                </h2>
            </div>

            {/* Add Policy Form */}
            <form onSubmit={handleAdd} className="bg-gray-800 p-6 rounded-xl border border-gray-700 mb-8 flex gap-4 items-end">
                <div className="flex-1">
                    <label className="block text-xs text-gray-400 mb-1">Domain Pattern (e.g., youtube.com)</label>
                    <input
                        type="text"
                        value={newPattern}
                        onChange={e => setNewPattern(e.target.value)}
                        className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none"
                        placeholder="example.com"
                        required
                    />
                </div>
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Type</label>
                    <select
                        value={newType}
                        onChange={e => setNewType(e.target.value)}
                        className="bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white outline-none"
                    >
                        <option value="BLACKLIST">BLACKLIST (Block)</option>
                        <option value="WHITELIST">WHITELIST (Force)</option>
                    </select>
                </div>
                <button type="submit" className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium flex items-center gap-2">
                    <Plus size={18} /> Add Policy
                </button>
            </form>

            {/* Policies List */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-900/50 text-gray-400 text-sm">
                        <tr>
                            <th className="p-4">Pattern</th>
                            <th className="p-4">Type</th>
                            <th className="p-4">Created At</th>
                            <th className="p-4">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {policies.length === 0 ? (
                            <tr><td colSpan={4} className="p-8 text-center text-gray-500">No policies defined.</td></tr>
                        ) : (
                            policies.map(p => (
                                <tr key={p.id} className="hover:bg-gray-750">
                                    <td className="p-4 text-white font-mono">{p.pattern}</td>
                                    <td className="p-4">
                                        {p.type === 'BLACKLIST' ? (
                                            <span className="text-red-400 text-xs font-bold border border-red-500/30 bg-red-500/10 px-2 py-1 rounded flex w-fit items-center gap-1">
                                                <ShieldAlert size={12} /> BLACKLIST
                                            </span>
                                        ) : (
                                            <span className="text-green-400 text-xs font-bold border border-green-500/30 bg-green-500/10 px-2 py-1 rounded flex w-fit items-center gap-1">
                                                <CheckCircle size={12} /> WHITELIST
                                            </span>
                                        )}
                                    </td>
                                    <td className="p-4 text-gray-500 text-sm">
                                        {format(new Date(p.created_at), 'yyyy-MM-dd HH:mm')}
                                    </td>
                                    <td className="p-4">
                                        <button onClick={() => handleDelete(p.id)} className="text-gray-500 hover:text-red-400">
                                            <Trash size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
