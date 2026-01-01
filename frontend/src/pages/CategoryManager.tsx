import { useEffect, useState } from 'react';
import axios from 'axios';
import { Plus, Edit, Trash2, AlertTriangle, Shield, Check, X } from 'lucide-react';

interface Category {
    id: number;
    name: string;
    description: string;
    is_system: boolean;
    count: number;
}

export default function CategoryManager() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingCategory, setEditingCategory] = useState<Category | null>(null);

    // Form State
    const [formData, setFormData] = useState({ name: '', description: '' });

    // Stats State
    const [stats, setStats] = useState<{ total: number, categories: { name: string, count: number, percent: number }[] }>({ total: 0, categories: [] });

    const fetchCategories = async () => {
        setLoading(true);
        try {
            const [catRes, statRes] = await Promise.all([
                axios.get('/api/v2/categories/'),
                axios.get('/api/v2/categories/stats')
            ]);
            setCategories(catRes.data);
            setStats({ total: statRes.data.total_items, categories: statRes.data.categories });
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCategories();
    }, []);

    const handleEdit = (cat: Category) => {
        setEditingCategory(cat);
        setFormData({ name: cat.name, description: cat.description || '' });
        setIsModalOpen(true);
    };

    const handleAdd = () => {
        setEditingCategory(null);
        setFormData({ name: '', description: '' });
        setIsModalOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingCategory) {
                // Update
                if (editingCategory.name !== formData.name && editingCategory.count > 0) {
                    if (!confirm(`Warning: Renaming this category will update ${editingCategory.count} items in the Knowledge Base. Continue?`)) {
                        return;
                    }
                }

                await axios.put(`/api/v2/categories/${editingCategory.id}`, formData);
                alert("Category updated successfully!");
            } else {
                // Create
                await axios.post('/api/v2/categories/', formData);
                alert("Category created successfully!");
            }
            setIsModalOpen(false);
            fetchCategories();
        } catch (e: any) {
            alert(e.response?.data?.detail || "Operation failed");
        }
    };

    const handleDelete = async (cat: Category) => {
        if (cat.is_system) {
            alert("System categories cannot be deleted.");
            return;
        }
        if (cat.count > 0) {
            alert(`Cannot delete '${cat.name}': It is currently used by ${cat.count} items.\nPlease reassign them first.`);
            return;
        }
        if (!confirm(`Are you sure you want to delete '${cat.name}'?`)) return;

        try {
            await axios.delete(`/api/v2/categories/${cat.id}`);
            fetchCategories();
        } catch (e: any) {
            alert(e.response?.data?.detail || "Delete failed");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Category Manager</h1>
                    <p className="text-gray-400 text-sm">Manage standard categories and maintain data consistency.</p>
                </div>
                <button
                    onClick={handleAdd}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    <Plus size={18} /> Add Category
                </button>
            </div>

            {/* Stats Chart (All Categories) */}
            {categories.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">
                        Category Distribution
                        <span className="text-sm font-normal text-gray-500 ml-2">
                            (Total: {stats.total.toLocaleString()} items)
                        </span>
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
                        {categories.sort((a, b) => b.count - a.count).map(cat => {
                            const percent = stats.total > 0 ? (cat.count / stats.total * 100) : 0;
                            return (
                                <div key={cat.id} className="space-y-1">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-gray-300 truncate pr-2" title={cat.name}>{cat.name}</span>
                                        <span className="text-gray-400 shrink-0">
                                            {cat.count.toLocaleString()} <span className="text-xs text-gray-500">({percent.toFixed(1)}%)</span>
                                        </span>
                                    </div>
                                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${cat.count > 0 ? 'bg-blue-500' : 'bg-gray-700'}`}
                                            style={{ width: `${Math.max(percent, 0)}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {loading ? (
                <div className="text-center py-10 text-gray-500">Loading categories...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categories.map(cat => (
                        <div key={cat.id} className="bg-gray-800 border border-gray-700 rounded-xl p-5 hover:border-gray-600 transition-colors">
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex items-center gap-2">
                                    <h3 className="text-lg font-semibold text-white">{cat.name}</h3>
                                    {cat.is_system && (
                                        <span className="bg-gray-700 text-gray-300 text-[10px] px-1.5 py-0.5 rounded flex items-center gap-1" title="System Category">
                                            <Shield size={10} /> System
                                        </span>
                                    )}
                                </div>
                                <div className="flex gap-1">
                                    <button
                                        onClick={() => handleEdit(cat)}
                                        className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                                        title="Edit"
                                    >
                                        <Edit size={16} />
                                    </button>
                                    {!cat.is_system && (
                                        <button
                                            onClick={() => handleDelete(cat)}
                                            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg"
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>

                            <p className="text-gray-400 text-sm h-10 line-clamp-2 mb-4">
                                {cat.description || "No description provided."}
                            </p>

                            <div className="flex items-center justify-between pt-4 border-t border-gray-700/50">
                                <span className="text-xs text-gray-500">KB Usage</span>
                                <span className={`text-sm font-medium ${cat.count > 0 ? "text-blue-400" : "text-gray-600"}`}>
                                    {cat.count.toLocaleString()} Items
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create/Edit Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
                    <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-white">
                                {editingCategory ? "Edit Category" : "New Category"}
                            </h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Category Name</label>
                                <input
                                    type="text"
                                    required
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
                                <textarea
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white h-24 focus:outline-none focus:border-blue-500"
                                    value={formData.description}
                                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="Brief description of this category..."
                                />
                            </div>

                            {editingCategory && editingCategory.count > 0 && editingCategory.name !== formData.name && (
                                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 flex gap-3 text-sm text-blue-200">
                                    <AlertTriangle className="shrink-0 text-blue-400" size={18} />
                                    <div>
                                        <p className="font-semibold text-blue-400">Cascade Update Warning</p>
                                        <p>Changing the name will automatically update all {editingCategory.count} items associated with this category.</p>
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors flex items-center justify-center gap-2"
                                >
                                    <Check size={18} /> Save Category
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
