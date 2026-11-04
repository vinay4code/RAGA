import React from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  MessageSquareText, 
  BarChart3, 
  ShieldCheck, 
  FileText, 
  Database,
  Sparkles
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, stats }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen, count: stats?.total_documents },
    { id: 'chat', label: 'AI Assistant', icon: MessageSquareText },
    { id: 'evaluation', label: 'Evaluation', icon: BarChart3 },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col justify-between select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="font-semibold text-white tracking-tight text-sm flex items-center gap-1.5">
              Enterprise RAG
              <span className="text-[10px] bg-blue-500/20 text-blue-400 font-mono px-1.5 py-0.5 rounded border border-blue-500/30">MVP</span>
            </div>
            <div className="text-[11px] text-slate-400">Documentation Assistant</div>
          </div>
        </div>

        {/* Navigation Menu */}
        <div className="px-3 py-6 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
            Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.count !== undefined && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-medium ${
                    isActive ? 'bg-blue-700/80 text-white' : 'bg-slate-800 text-slate-300'
                  }`}>
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center gap-2 mb-2 text-xs font-medium text-slate-300">
          <Database className="h-3.5 w-3.5 text-emerald-400" />
          <span>Active RAG Engine</span>
        </div>
        <div className="space-y-1.5 text-[11px] text-slate-400">
          <div className="flex justify-between items-center">
            <span>Provider:</span>
            <span className="font-mono text-slate-200 capitalize font-medium">
              {stats?.system_status?.llm_provider || 'Local Engine'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Embeddings:</span>
            <span className="font-mono text-slate-200 text-[10px]">MiniLM-L6-v2</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Retrieval:</span>
            <span className="font-mono text-emerald-400 text-[10px]">Hybrid (Dense+BM25)</span>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Zero Hallucination Grounding</span>
        </div>
      </div>
    </aside>
  );
}
