import React from 'react';
import { X, FileText, CheckCircle2, Bookmark, Layers, Sparkles, ExternalLink } from 'lucide-react';

export default function EvidenceDrawer({ isOpen, onClose, evidenceList = [], activeChunkId = null }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-white border-l border-slate-200 shadow-2xl flex flex-col transition-all duration-300">
      {/* Header */}
      <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-semibold">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900">Retrieved Evidence Passages</h3>
            <p className="text-xs text-slate-500">
              {evidenceList.length} passage{evidenceList.length !== 1 ? 's' : ''} retrieved via Hybrid Search & Reranking
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Content list */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {evidenceList.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            No evidence passages retrieved for this response.
          </div>
        ) : (
          evidenceList.map((chunk, index) => {
            const isTargeted = activeChunkId === chunk.chunk_id;
            const scorePercent = Math.round((chunk.relevance_score || 0) * 100);

            return (
              <div
                key={chunk.chunk_id || index}
                id={`chunk-${chunk.chunk_id}`}
                className={`rounded-xl border p-4 transition-all ${
                  isTargeted
                    ? 'border-blue-500 bg-blue-50/40 ring-2 ring-blue-500/20'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                {/* Passage Header */}
                <div className="flex items-start justify-between gap-3 mb-2.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      #{index + 1}
                    </span>
                    <span className="font-semibold text-xs text-slate-900 flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-blue-600" />
                      {chunk.document_name}
                    </span>
                    {chunk.version && (
                      <span className="text-[10px] bg-slate-100 text-slate-600 font-mono px-1.5 py-0.5 rounded">
                        v{chunk.version}
                      </span>
                    )}
                  </div>

                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                    chunk.retrieval_method === 'hybrid'
                      ? 'bg-purple-100 text-purple-700'
                      : chunk.retrieval_method === 'semantic'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-emerald-100 text-emerald-700'
                  }`}>
                    {chunk.retrieval_method || 'Hybrid'}
                  </span>
                </div>

                {/* Metadata Pills */}
                <div className="flex items-center gap-3 text-xs text-slate-500 mb-3 flex-wrap">
                  <div className="flex items-center gap-1">
                    <Bookmark className="h-3 w-3 text-slate-400" />
                    <span>Section: <strong className="text-slate-700">{chunk.section || 'General'}</strong></span>
                  </div>
                  {chunk.page_number && (
                    <div>
                      Page: <strong className="text-slate-700">{chunk.page_number}</strong>
                    </div>
                  )}
                  {chunk.last_updated && (
                    <div>
                      Date: <span className="font-mono">{chunk.last_updated}</span>
                    </div>
                  )}
                </div>

                {/* Relevance Score Bar */}
                <div className="mb-3">
                  <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                    <span>Relevance Match</span>
                    <span className="font-mono text-blue-700">{scorePercent}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500"
                      style={{ width: `${scorePercent}%` }}
                    />
                  </div>
                </div>

                {/* Passage Text */}
                <div className="bg-slate-50/80 rounded-lg p-3 text-xs leading-relaxed text-slate-700 font-mono whitespace-pre-wrap border border-slate-200/60">
                  {chunk.content}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
