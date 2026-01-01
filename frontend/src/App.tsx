import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Explorer from './pages/Explorer';
import Pipeline from './pages/Pipeline';
import Policies from './pages/Policies';
import Chat from './pages/Chat';
import KnowledgeBase from './pages/KnowledgeBase';

import CategoryManager from './pages/CategoryManager';
import FeedManager from './pages/FeedManager';

function App() {
    return (
        <Router>
            <Layout>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/explorer" element={<Explorer />} />
                    <Route path="/kb" element={<KnowledgeBase />} />
                    <Route path="/pipeline" element={<Pipeline />} />
                    <Route path="/policies" element={<Policies />} />
                    <Route path="/categories" element={<CategoryManager />} />
                    <Route path="/feeds" element={<FeedManager />} />
                    <Route path="/chat" element={<Chat />} />

                    {/* Placeholders for future steps */}
                    <Route path="/settings" element={<div className="text-gray-500">Settings Coming Soon</div>} />

                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Layout>
        </Router>
    );
}

export default App;
