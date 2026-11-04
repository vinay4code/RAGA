import React from 'react';
import { X, FileText, Hash, Calendar, Layers, CheckCircle2 } from 'lucide-react';

export default function DocumentModal({ isOpen, onClose, docData }) {
  if (!isOpen || !docData) return null;

  const { document: doc, chunks = [] } = docData;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-3xl max-h-[85vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-base">{doc.filename}</h3>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="uppercase font-mono font-semibold">{doc.format}</span>
                <span>•</span>
                <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                <span>•</span>
                <span className="flex items-center gap-1 text-emerald-600 font-medium">
                  <CheckCircle2 className="h-3 w-3" /> Indexed ({chunks.length} chunks)
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Chunks List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Document Chunks & Vector Metadata ({chunks.length})
          </div>

          {chunks.length === 0 ? (
            <div className="text-center py-8 text-sm text-slate-400">
              No chunks recorded for this document.
            </div>
          ) : (
            chunks.map((chunk, idx) => (
              <div
                key={chunk.chunk_id || idx}
                className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 hover:bg-white transition"
              >
                <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-200/60 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold bg-slate-200 text-slate-700 px-2 py-0.5 rounded">
                      Chunk {chunk.chunk_index}
                    </span>
                    <span className="text-slate-600">
                      Section: <strong className="text-slate-800">{chunk.section_heading || 'General'}</strong>
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-500 font-mono text-[11px]">
                    {chunk.page_number && <span>Page: {chunk.page_number}</span>}
                    <span>Tokens: {chunk.token_count}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-mono whitespace-pre-wrap">
                  {chunk.content}
                </p>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
