import React from 'react';

export default function MarkdownView({ content }) {
  if (!content) return null;

  // Split by double newlines or block elements
  const blocks = content.split('\n\n');

  return (
    <div className="space-y-2.5 text-xs text-slate-800 leading-relaxed font-sans">
      {blocks.map((block, idx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Header 3: ###
        if (trimmed.startsWith('### ')) {
          return (
            <h4 key={idx} className="font-bold text-slate-900 text-xs tracking-tight pt-1 text-blue-900 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              {trimmed.replace(/^###\s+/, '')}
            </h4>
          );
        }

        // Header 2: ##
        if (trimmed.startsWith('## ')) {
          return (
            <h3 key={idx} className="font-bold text-slate-900 text-sm tracking-tight pt-1">
              {trimmed.replace(/^##\s+/, '')}
            </h3>
          );
        }

        // Blockquote: >
        if (trimmed.startsWith('> ')) {
          return (
            <div key={idx} className="border-l-2 border-amber-500 bg-amber-50/70 p-2.5 rounded-r-lg text-amber-900 text-xs italic">
              {trimmed.replace(/^>\s+/, '')}
            </div>
          );
        }

        // Unordered list: lines starting with - or *
        if (trimmed.split('\n').every(line => line.trim().startsWith('- ') || line.trim().startsWith('* ') || !line.trim())) {
          const items = trimmed.split('\n').filter(line => line.trim().length > 0);
          return (
            <ul key={idx} className="space-y-1.5 pl-3">
              {items.map((item, itemIdx) => {
                const itemText = item.trim().replace(/^[-*]\s+/, '');
                return (
                  <li key={itemIdx} className="flex items-start gap-2 text-slate-700">
                    <span className="text-blue-500 font-bold leading-none mt-1">•</span>
                    <span>{renderInlineFormatting(itemText)}</span>
                  </li>
                );
              })}
            </ul>
          );
        }

        // Regular paragraph with inline formatting
        return (
          <p key={idx} className="text-slate-800">
            {renderInlineFormatting(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

function renderInlineFormatting(text) {
  // Regex to split by bold (**text**), inline code (`code`), or citation bracket [Doc: ...]
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[(?:Doc|Document|Source):[^\]]+\])/g);

  return parts.map((part, i) => {
    if (!part) return null;

    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
    }

    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 font-mono text-[11px] border border-slate-200">
          {part.slice(1, -1)}
        </code>
      );
    }

    if (part.startsWith('[Doc:') || part.startsWith('[Document:') || part.startsWith('[Source:')) {
      return (
        <span key={i} className="inline-flex items-center text-[10px] font-mono font-medium text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.2 rounded ml-1">
          {part}
        </span>
      );
    }

    return part;
  });
}
