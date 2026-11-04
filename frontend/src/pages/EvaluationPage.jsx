import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Play, 
  Download, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  RefreshCw, 
  ChevronDown, 
  ChevronRight,
  ShieldAlert,
  FileCheck,
  TrendingUp,
  Cpu
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from 'recharts';
import { runEvaluationSuite, fetchEvaluationResults } from '../services/api';

export default function EvaluationPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [evalData, setEvalData] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    try {
      const res = await fetchEvaluationResults();
      if (res.latest) {
        setEvalData(res.latest.details || res.latest);
      }
    } catch (err) {
      console.error('Failed to load evaluation results:', err);
    }
  };

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const results = await runEvaluationSuite();
      setEvalData(results);
    } catch (err) {
      setError(err.message || 'Evaluation run failed');
    } finally {
      setIsRunning(false);
    }
  };

  const toggleRow = (idx) => {
    setExpandedRows(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const handleExport = () => {
    if (!evalData) return;
    const blob = new Blob([JSON.stringify(evalData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evaluation_report_${evalData.id || 'latest'}.json`;
    a.click();
  };

  // Recharts Data preparation
  const metricsChartData = evalData ? [
    { metric: 'Recall@K', value: Math.round(evalData.recall_at_k * 100), benchmark: 80 },
    { metric: 'Precision@K', value: Math.round(evalData.precision_at_k * 100), benchmark: 60 },
    { metric: 'MRR', value: Math.round(evalData.mrr * 100), benchmark: 75 },
    { metric: 'Citation Acc', value: Math.round(evalData.citation_accuracy * 100), benchmark: 80 },
    { metric: 'Abstention Acc', value: Math.round(evalData.abstention_accuracy * 100), benchmark: 90 },
    { metric: 'Groundedness', value: Math.round((evalData.groundedness_score || 1) * 100), benchmark: 85 }
  ] : [];

  // Group by question type for category breakdown chart
  const categoryStats = {};
  if (evalData && evalData.results) {
    evalData.results.forEach(r => {
      const type = r.question_type || 'other';
      if (!categoryStats[type]) {
        categoryStats[type] = { total: 0, passed: 0 };
      }
      categoryStats[type].total += 1;
      if (r.answerability_correct && (r.r_at_k > 0 || !r.answerable)) {
        categoryStats[type].passed += 1;
      }
    });
  }

  const categoryChartData = Object.keys(categoryStats).map(cat => ({
    category: cat.replace('_', ' '),
    accuracy: Math.round((categoryStats[cat].passed / categoryStats[cat].total) * 100)
  }));

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Empirical Evaluation Benchmark
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Systematic evaluation across 7 critical scenarios: Direct, Paraphrased, Multi-Doc, Conflicting, Version-Sensitive, Ambiguous, and Unanswerable queries.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExport}
            disabled={!evalData}
            className="flex items-center gap-2 px-3.5 py-2 bg-white text-slate-700 border border-slate-200 rounded-xl text-xs font-medium hover:bg-slate-50 transition disabled:opacity-40"
          >
            <Download className="h-3.5 w-3.5" />
            Export Report
          </button>
          <button
            onClick={handleRunEvaluation}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-medium hover:bg-blue-700 shadow-sm shadow-blue-600/20 transition disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Executing Suite...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                Run Benchmark Suite
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/90 p-4 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Cards Grid */}
      {evalData && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Total Questions
            </div>
            <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
              {evalData.num_questions}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Labelled dataset</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Recall@K
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
              {Math.round(evalData.recall_at_k * 100)}%
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Target passages found</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Precision@K
            </div>
            <div className="text-2xl font-bold font-mono text-blue-600 mt-1">
              {Math.round(evalData.precision_at_k * 100)}%
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Retrieved relevance</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              MRR
            </div>
            <div className="text-2xl font-bold font-mono text-indigo-600 mt-1">
              {evalData.mrr}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Mean reciprocal rank</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Citation Acc
            </div>
            <div className="text-2xl font-bold font-mono text-purple-600 mt-1">
              {Math.round(evalData.citation_accuracy * 100)}%
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Verifiable passages</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Abstention Acc
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
              {Math.round(evalData.abstention_accuracy * 100)}%
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Zero hallucination</div>
          </div>
        </div>
      )}

      {/* Visual Analytics Charts */}
      {evalData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main Benchmark Metrics Chart */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-900 text-sm">
                System Quality & Retrieval Metrics
              </h3>
              <span className="text-[11px] font-mono text-slate-400">Score vs Target</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricsChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
                  <Tooltip
                    formatter={(value) => [`${value}%`]}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="value" name="Measured Value" fill="#2563eb" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="benchmark" name="Target Baseline" fill="#94a3b8" radius={[6, 6, 0, 0]} opacity={0.4} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category Breakdown Chart */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-900 text-sm">
                Performance by Scenario Category
              </h3>
              <span className="text-[11px] font-mono text-slate-400">7 Scenarios</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="category" tick={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
                  <Tooltip
                    formatter={(value) => [`${value}% Accuracy`]}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="accuracy" name="Scenario Accuracy" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Per-Question Verification Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 text-sm">
              Question-by-Question Benchmark Verification
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any question to inspect retrieved citations, expected sources, and answerability verdict.
            </p>
          </div>
          <span className="text-xs bg-slate-100 text-slate-600 font-mono px-2.5 py-1 rounded-full">
            {evalData?.results?.length || 0} Test Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
              <tr>
                <th className="w-8 px-4 py-3.5"></th>
                <th className="px-4 py-3.5">Test Question</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Expected Sources</th>
                <th className="px-4 py-3.5">Confidence</th>
                <th className="px-4 py-3.5">MRR</th>
                <th className="px-4 py-3.5 text-right">Verdict</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {(!evalData || !evalData.results) ? (
                <tr>
                  <td colSpan="7" className="text-center py-12 text-slate-400">
                    No evaluation data loaded. Click "Run Benchmark Suite" to evaluate the RAG pipeline.
                  </td>
                </tr>
              ) : (
                evalData.results.map((r, idx) => {
                  const isExpanded = !!expandedRows[idx];
                  const isPassed = r.answerability_correct && (r.r_at_k > 0 || !r.answerable);

                  return (
                    <React.Fragment key={idx}>
                      <tr 
                        onClick={() => toggleRow(idx)}
                        className="hover:bg-slate-50/80 transition cursor-pointer select-none"
                      >
                        <td className="px-4 py-3.5 text-slate-400">
                          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </td>
                        <td className="px-4 py-3.5 font-medium text-slate-900 max-w-xs">
                          {r.question}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="capitalize font-mono text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                            {r.question_type?.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-slate-500 font-mono text-[11px] truncate max-w-xs">
                          {r.expected_sources?.length > 0 ? r.expected_sources.join(', ') : 'None (Unanswerable)'}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                            r.confidence === 'HIGH' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                            r.confidence === 'MEDIUM' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                            'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {r.confidence}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-mono">
                          {r.reciprocal_rank}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <span className={`inline-flex items-center gap-1 font-semibold text-[11px] px-2 py-0.5 rounded-full ${
                            isPassed ? 'text-emerald-700 bg-emerald-50' : 'text-rose-700 bg-rose-50'
                          }`}>
                            {isPassed ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                            {isPassed ? 'Pass' : 'Fail'}
                          </span>
                        </td>
                      </tr>

                      {/* Expandable Details Row */}
                      {isExpanded && (
                        <tr className="bg-slate-50/90">
                          <td colSpan="7" className="px-8 py-4 space-y-3">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="bg-white p-3.5 rounded-xl border border-slate-200">
                                <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">
                                  Generated Grounded Answer
                                </div>
                                <div className="text-xs text-slate-800 whitespace-pre-wrap leading-relaxed font-sans">
                                  {r.actual_answer}
                                </div>
                              </div>

                              <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-2">
                                <div className="text-[10px] uppercase font-bold text-slate-400">
                                  Retrieved Citations & Sources
                                </div>
                                {r.citations && r.citations.length > 0 ? (
                                  <div className="space-y-1.5">
                                    {r.citations.map((c, cIdx) => (
                                      <div key={cIdx} className="text-[11px] font-mono text-slate-700 bg-slate-50 p-2 rounded border border-slate-200/60">
                                        <div className="font-semibold text-blue-700">{c.document_name}</div>
                                        <div className="text-slate-500">Section: {c.section} {c.page_number ? `| Page ${c.page_number}` : ''}</div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-xs text-slate-400 italic">
                                    No citations generated (expected for unanswerable query).
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
