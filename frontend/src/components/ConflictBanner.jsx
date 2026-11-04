import React from 'react';
import { AlertTriangle, GitCompare, Info } from 'lucide-react';

export default function ConflictBanner({ conflict }) {
  if (!conflict || !conflict.has_conflict) return null;

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50/90 p-4 text-amber-900 shadow-xs mb-3">
      <div className="flex items-start gap-3">
        <div className="p-1.5 rounded-lg bg-amber-200/80 text-amber-800 shrink-0">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-sm text-amber-950">
              Conflicting Documentation Detected
            </h4>
            <span className="text-[10px] uppercase font-bold bg-amber-200 text-amber-800 px-2 py-0.5 rounded">
              {conflict.conflict_type || 'Policy Discrepancy'}
            </span>
          </div>

          <p className="text-xs text-amber-800 mt-1 leading-relaxed">
            {conflict.warning}
          </p>

          {conflict.details && (
            <div className="mt-2 text-xs bg-white/70 rounded-lg p-2.5 border border-amber-200/80 font-mono text-amber-900">
              {conflict.details}
            </div>
          )}

          {conflict.sources && conflict.sources.length > 0 && (
            <div className="mt-2.5 flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-medium text-amber-700">Divergent Sources:</span>
              {conflict.sources.map((src, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 text-[11px] bg-amber-100 border border-amber-300/80 rounded px-2 py-0.5 font-medium text-amber-900"
                >
                  <GitCompare className="h-3 w-3 text-amber-700" />
                  {src.document} (v{src.version || '1.0'})
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
