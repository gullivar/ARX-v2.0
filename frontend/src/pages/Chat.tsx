import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, Search, Database } from 'lucide-react';

export default function Chat() {
    const [query, setQuery] = useState('');
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [mode, setMode] = useState<'rag' | 'kb-search'>('rag');

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [history, loading]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        const newMsg = { role: 'user', content: query };
        setHistory(prev => [...prev, newMsg]);
        setQuery('');
        setLoading(true);

        try {
            const res = await axios.post('/api/v2/intelligence/chat', {
                query: newMsg.content,
                mode: mode
            });
            setHistory(prev => [...prev, {
                role: 'bot',
                content: res.data.answer,
                sources: res.data.sources,
                mode: res.data.mode
            }]);
        } catch (e) {
            setHistory(prev => [...prev, { role: 'bot', content: 'Sorry, I encountered an error.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-140px)]">
            <div className="mb-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        {mode === 'rag' ? <Bot className="text-purple-400" /> : <Database className="text-green-400" />}
                        {mode === 'rag' ? 'AI Intel Analyst' : 'KB Data Inspector'}
                    </h2>
                    <p className="text-gray-400 text-sm">
                        {mode === 'rag'
                            ? 'Deep analysis using LLM + KB + Pipeline Data.'
                            : 'Direct semantic search into ChromaDB Vector Store.'}
                    </p>
                </div>

                {/* Mode Toggle */}
                <div className="bg-gray-800 p-1 rounded-lg border border-gray-700 flex">
                    <button
                        onClick={() => setMode('rag')}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${mode === 'rag' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <Bot size={16} /> AI Analysis
                    </button>
                    <button
                        onClick={() => setMode('kb-search')}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${mode === 'kb-search' ? 'bg-green-600 text-white' : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <Search size={16} /> KB Lookup
                    </button>
                </div>
            </div>

            <div className="flex-1 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {history.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
                            {mode === 'rag' ? <Bot size={48} className="mb-4" /> : <Database size={48} className="mb-4" />}
                            <p>Try asking: "Is torrenttt213.top malicious?"</p>
                        </div>
                    )}

                    {history.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] rounded-lg p-4 ${msg.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-700 text-gray-200'
                                }`}>
                                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-600/50">
                                    <span className="text-xs font-bold uppercase opacity-70">
                                        {msg.role === 'user' ? 'You' : (msg.mode === 'kb-search' ? 'KB Inspector' : 'AI Analyst')}
                                    </span>
                                </div>
                                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>

                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-3 pt-2 border-t border-gray-600 text-xs text-gray-400">
                                        <strong>Ref:</strong> {msg.sources.slice(0, 3).join(', ')}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-gray-700 rounded-lg p-4 text-gray-400 animate-pulse text-sm">
                                {mode === 'rag' ? 'Analyzing patterns...' : 'Querying Vector DB...'}
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <form onSubmit={handleSend} className="p-4 bg-gray-900 border-t border-gray-700 flex gap-4">
                    <input
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder={mode === 'rag' ? "Ask about threats..." : "Search for signatures..."}
                        className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-blue-500 outline-none"
                    />
                    <button type="submit" disabled={loading} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white disabled:opacity-50">
                        <Send size={18} />
                    </button>
                </form>
            </div>
        </div>
    );
}
