import React from 'react';
import { 
  FileText, 
  Layers, 
  MessageSquare, 
  ShieldCheck, 
  ArrowUpRight, 
  UploadCloud, 
  BarChart2, 
  CheckCircle2, 
  AlertCircle,
  Database,
  Cpu,
  Search,
  ExternalLink
} from 'lucide-react';

export default function DashboardPage({ stats, setActiveTab, onInspectDoc }) {
  const statCards = [
    {
      title: 'Total Documents',
      value: stats?.total_documents || 0,
      sub: `${stats?.indexed_documents || 0} indexed & active`,
      icon: FileText,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      title: 'Indexed Chunks',
      value: stats?.total_chunks || 0,
      sub: '500-800 tokens / chunk',
      icon: Layers,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    {
      title: 'Questions Asked',
      value: stats?.total_questions || 0,
      sub: 'Evidence-grounded sessions',
      icon: MessageSquare,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      title: 'Retrieval Grounding Rate',
      value: `${stats?.retrieval_success_rate || 100}%`,
      sub: 'Zero hallucination guard',
      icon: ShieldCheck,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Top Welcome / Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Enterprise Documentation Intelligence
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Production-quality evidence-grounded Q&A system with verified source citations & conflict detection.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('knowledge')}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 shadow-sm shadow-blue-600/20 transition"
          >
            <UploadCloud className="h-4 w-4" />
            Upload Documents
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className="flex items-center gap-2 px-4 py-2.5 bg-white text-slate-700 border border-slate-200 rounded-xl text-sm font-medium hover:bg-slate-50 shadow-xs transition"
          >
            <MessageSquare className="h-4 w-4" />
            Ask Question
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className="flex items-center gap-2 px-4 py-2.5 bg-white text-slate-700 border border-slate-200 rounded-xl text-sm font-medium hover:bg-slate-50 shadow-xs transition"
          >
            <BarChart2 className="h-4 w-4" />
            View Benchmark
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 transition"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {card.title}
                </span>
                <div className={`p-2 rounded-xl ${card.bg} ${card.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-3xl font-bold tracking-tight text-slate-900 font-mono">
                  {card.value}
                </div>
                <div className="text-xs text-slate-400 mt-1">{card.sub}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Architecture & Evaluation Snapshot Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Architecture Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-slate-100 text-slate-700">
                  <Cpu className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-slate-900 text-sm">System Pipeline Architecture</h3>
              </div>
              <span className="text-[11px] font-mono bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
                Healthy
              </span>
            </div>

            <div className="mt-4 space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-500">LLM Generation:</span>
                <span className="font-semibold text-slate-800 capitalize font-mono">
                  {stats?.system_status?.llm_provider || 'Local Grounded Engine'}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Embedding Model:</span>
                <span className="font-semibold text-slate-800 font-mono">all-MiniLM-L6-v2 (384-d)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Vector Storage:</span>
                <span className="font-semibold text-slate-800 font-mono">ChromaDB (HNSW Cosine)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Keyword Retrieval:</span>
                <span className="font-semibold text-slate-800 font-mono">BM25Okapi (In-Memory)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Rank Fusion:</span>
                <span className="font-semibold text-blue-700 font-mono">Reciprocal Rank Fusion (RRF)</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Security: Prompt injection defense active</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
        </div>

        {/* Latest Evaluation Metrics Snapshot */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-blue-50 text-blue-700">
                  <BarChart2 className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm">Empirical Evaluation Snapshot</h3>
                  <p className="text-[11px] text-slate-400">Measured against labelled test benchmark dataset</p>
                </div>
              </div>
              <button
                onClick={() => setActiveTab('evaluation')}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
              >
                Full Details <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>

            {stats?.latest_evaluation ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-slate-500 text-[11px] font-medium">Mean Reciprocal Rank</div>
                  <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                    {stats.latest_evaluation.mrr}
                  </div>
                  <div className="text-[10px] text-emerald-600 font-medium mt-0.5">Top-1 rank quality</div>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-slate-500 text-[11px] font-medium">Recall@K</div>
                  <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                    {Math.round(stats.latest_evaluation.recall_at_k * 100)}%
                  </div>
                  <div className="text-[10px] text-emerald-600 font-medium mt-0.5">Relevant evidence hit</div>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-slate-500 text-[11px] font-medium">Abstention Accuracy</div>
                  <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                    {Math.round(stats.latest_evaluation.abstention_accuracy * 100)}%
                  </div>
                  <div className="text-[10px] text-emerald-600 font-medium mt-0.5">Refused unanswerable</div>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="text-slate-500 text-[11px] font-medium">Citation Accuracy</div>
                  <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                    {Math.round(stats.latest_evaluation.citation_accuracy * 100)}%
                  </div>
                  <div className="text-[10px] text-emerald-600 font-medium mt-0.5">Verified references</div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-sm">
                No evaluation run recorded yet. Click "View Benchmark" to execute the test suite.
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Evaluation Dataset: test_questions.json</span>
            <span>7 Question Categories Tested</span>
          </div>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900 text-sm">Active Knowledge Documents</h3>
            <span className="text-xs bg-slate-100 text-slate-600 font-mono px-2 py-0.5 rounded-full">
              {stats?.recent_documents?.length || 0}
            </span>
          </div>
          <button
            onClick={() => setActiveTab('knowledge')}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
          >
            Manage Knowledge Base <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/75 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
              <tr>
                <th className="px-6 py-3">Document Name</th>
                <th className="px-6 py-3">Format</th>
                <th className="px-6 py-3">Chunks</th>
                <th className="px-6 py-3">Size</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {(!stats?.recent_documents || stats.recent_documents.length === 0) ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-slate-400">
                    No documents uploaded yet.
                  </td>
                </tr>
              ) : (
                stats.recent_documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-3.5 font-medium text-slate-900 flex items-center gap-2.5">
                      <FileText className="h-4 w-4 text-blue-600 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="uppercase font-mono text-[11px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                        {doc.format}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono font-medium">
                      {doc.num_chunks}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-slate-500">
                      {(doc.size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-2 py-0.5 rounded-full text-[11px] font-medium">
                        <CheckCircle2 className="h-3 w-3" /> Indexed
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={() => onInspectDoc(doc.id)}
                        className="text-blue-600 hover:text-blue-800 font-medium hover:underline text-[11px]"
                      >
                        Inspect Chunks
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
