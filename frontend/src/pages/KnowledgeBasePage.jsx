import React, { useState } from 'react';
import { 
  UploadCloud, 
  Search, 
  Filter, 
  FileText, 
  Trash2, 
  Layers, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Eye,
  FileCode,
  FileCheck
} from 'lucide-react';
import { uploadDocuments, deleteDocument } from '../services/api';

export default function KnowledgeBasePage({ documents = [], onRefresh, onInspectDoc }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFormat, setSelectedFormat] = useState('ALL');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Filtered documents
  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (doc.title && doc.title.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesFormat = selectedFormat === 'ALL' || doc.format.toUpperCase() === selectedFormat;
    return matchesSearch && matchesFormat;
  });

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await uploadDocuments(files);
      const successful = res.uploaded_documents.filter(d => d.status === 'indexed');
      const duplicates = res.uploaded_documents.filter(d => d.message && d.message.includes('Duplicate'));
      const failed = res.uploaded_documents.filter(d => d.status === 'failed');

      let msg = '';
      if (successful.length > 0) msg += `Successfully indexed ${successful.length} document(s). `;
      if (duplicates.length > 0) msg += `${duplicates.length} duplicate(s) identified. `;
      if (failed.length > 0) msg += `${failed.length} failed: ${failed.map(f => f.error).join(', ')}`;

      setUploadSuccess(msg);
      if (onRefresh) onRefresh();
    } catch (err) {
      setUploadError(err.message || 'Failed to upload documents');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All chunks and vector indexes will be removed.`)) {
      return;
    }
    try {
      await deleteDocument(docId);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const getFormatBadge = (fmt) => {
    const format = fmt.toLowerCase();
    switch (format) {
      case 'pdf':
        return <span className="bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-mono font-bold px-2 py-0.5 rounded">PDF</span>;
      case 'html':
      case 'htm':
        return <span className="bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-mono font-bold px-2 py-0.5 rounded">HTML</span>;
      case 'md':
      case 'markdown':
        return <span className="bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-mono font-bold px-2 py-0.5 rounded">MD</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 text-[10px] font-mono font-bold px-2 py-0.5 rounded">TXT</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Enterprise Knowledge Base
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage organization documentation, inspect chunk boundaries, and synchronize vector indices.
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3.5 py-2 bg-white text-slate-700 border border-slate-200 rounded-xl text-xs font-medium hover:bg-slate-50 transition self-start"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {/* Upload Drag & Drop Area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFileUpload(e.dataTransfer.files);
        }}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all bg-white ${
          isDragging ? 'border-blue-500 bg-blue-50/50' : 'border-slate-200 hover:border-slate-300'
        }`}
      >
        <div className="max-w-md mx-auto space-y-3">
          <div className="h-12 w-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-inner">
            <UploadCloud className="h-6 w-6" />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-900 cursor-pointer hover:text-blue-600">
              Click to upload documents
              <input
                type="file"
                multiple
                accept=".pdf,.html,.htm,.md,.markdown,.txt"
                className="hidden"
                disabled={isUploading}
                onChange={(e) => handleFileUpload(e.target.files)}
              />
            </label>
            <span className="text-sm text-slate-500"> or drag and drop multiple files</span>
          </div>
          <p className="text-xs text-slate-400">
            Supported formats: PDF, HTML, Markdown (.md), Plain Text (.txt) • Up to 25MB each
          </p>
          {isUploading && (
            <div className="flex items-center justify-center gap-2 text-xs font-medium text-blue-600 animate-pulse pt-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              Processing, chunking, and embedding documents...
            </div>
          )}
        </div>
      </div>

      {/* Feedback Messages */}
      {uploadSuccess && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/90 p-4 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>{uploadSuccess}</span>
        </div>
      )}
      {uploadError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/90 p-4 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Controls Bar: Search & Format Filter */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search documents by name or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        {/* Format Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-medium text-slate-600 w-full sm:w-auto">
          {['ALL', 'PDF', 'MD', 'HTML', 'TXT'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => setSelectedFormat(fmt)}
              className={`px-3 py-1.5 rounded-lg transition ${
                selectedFormat === fmt
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'hover:text-slate-900'
              }`}
            >
              {fmt}
            </button>
          ))}
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">Document Title & Filename</th>
                <th className="px-6 py-3.5">Format</th>
                <th className="px-6 py-3.5">Chunks</th>
                <th className="px-6 py-3.5">Size</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Date Added</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-12 text-slate-400">
                    No matching documents found.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 text-xs">
                            {doc.title || doc.filename}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                            {doc.filename}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getFormatBadge(doc.format)}
                    </td>
                    <td className="px-6 py-4 font-mono font-medium">
                      {doc.num_chunks}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-500">
                      {(doc.size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
                        <CheckCircle2 className="h-3 w-3" /> Indexed
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-400 text-[11px] font-mono">
                      {doc.created_at ? doc.created_at.split('T')[0] : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onInspectDoc(doc.id)}
                          title="Inspect Chunks"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          title="Delete Document"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
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
