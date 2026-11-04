import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Copy, 
  ThumbsUp, 
  ThumbsDown, 
  Layers, 
  Sparkles, 
  RefreshCw,
  Plus,
  MessageSquare,
  Clock,
  ExternalLink
} from 'lucide-react';
import { sendChatMessage, fetchConversations, fetchConversationHistory } from '../services/api';
import ConflictBanner from '../components/ConflictBanner';
import MarkdownView from '../components/MarkdownView';

export default function ChatPage({ onOpenEvidence, stats }) {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackState, setFeedbackState] = useState({});
  const messagesEndRef = useRef(null);

  const suggestedQuestions = [
    {
      category: 'Direct Question',
      text: 'How can I reset my account password?'
    },
    {
      category: 'Conflict Detection',
      text: 'What is the maximum API request limit per hour?'
    },
    {
      category: 'Multi-Document',
      text: 'What happens if an API client exceeds the standard rate limit, and what is the overage fee for extra requests?'
    },
    {
      category: 'Troubleshooting',
      text: 'What are the troubleshooting steps when receiving error ERR-401?'
    },
    {
      category: 'Unanswerable / Fallback',
      text: 'What is the company reimbursement policy for international business travel meals?'
    }
  ];

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const convs = await fetchConversations();
      setConversations(convs);
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  };

  const handleSelectConversation = async (convId) => {
    setActiveConvId(convId);
    try {
      const data = await fetchConversationHistory(convId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Error fetching conversation messages:', err);
    }
  };

  const handleNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
    setInputQuery('');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || isLoading) return;

    // Add user message optimistically
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(query, activeConvId);
      if (!activeConvId && response.conversation_id) {
        setActiveConvId(response.conversation_id);
        loadConversations();
      }

      const asstMsg = {
        id: response.message?.id || `asst-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        confidence: response.confidence,
        confidence_score: response.confidence_score,
        conflict: response.conflict,
        citations: response.citations || [],
        retrieved_evidence: response.retrieved_evidence || [],
        created_at: new Date().toISOString()
      };

      setMessages(prev => [...prev, asstMsg]);
    } catch (err) {
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err.message || 'Unable to process question. Please check backend connection.'}`,
        confidence: 'LOW',
        citations: [],
        retrieved_evidence: [],
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setFeedbackState(prev => ({ ...prev, [id]: 'copied' }));
    setTimeout(() => {
      setFeedbackState(prev => ({ ...prev, [id]: null }));
    }, 2000);
  };

  const handleFeedback = (id, type) => {
    setFeedbackState(prev => ({ ...prev, [id]: type }));
  };

  const getConfidenceBadge = (confidence, score) => {
    const percent = score ? Math.round(score * 100) : null;
    switch (confidence) {
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5" /> High Confidence {percent ? `(${percent}%)` : ''}
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="h-3.5 w-3.5" /> Medium Confidence {percent ? `(${percent}%)` : ''}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
            <HelpCircle className="h-3.5 w-3.5" /> Low Confidence / Refusal
          </span>
        );
    }
  };

  return (
    <div className="flex h-full overflow-hidden bg-slate-50">
      {/* Conversations Sub-Sidebar */}
      <div className="w-72 bg-white border-r border-slate-200/80 flex flex-col justify-between shrink-0">
        <div>
          {/* Header */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Conversations
            </span>
            <button
              onClick={handleNewConversation}
              className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition flex items-center gap-1 text-xs font-medium"
            >
              <Plus className="h-3.5 w-3.5" />
              New
            </button>
          </div>

          {/* Conversation List */}
          <div className="p-2 space-y-1 overflow-y-auto max-h-[calc(100vh-180px)]">
            {conversations.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">
                No past sessions yet.
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`w-full text-left p-3 rounded-xl text-xs transition flex items-start gap-2.5 ${
                    activeConvId === conv.id
                      ? 'bg-blue-50 text-blue-900 font-semibold border border-blue-200/60'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0 text-slate-400 mt-0.5" />
                  <div className="truncate flex-1">
                    <div className="truncate font-medium">{conv.title}</div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      {conv.created_at?.split('T')[0]}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Sidebar Footer info */}
        <div className="p-4 border-t border-slate-100 text-[11px] text-slate-400">
          <div>Grounding Mode: Strict Evidence</div>
          <div className="text-slate-500 font-medium">Docs Indexed: {stats?.total_documents || 0}</div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          {messages.length === 0 ? (
            /* Welcome Banner and Suggested Questions */
            <div className="max-w-3xl mx-auto py-8 space-y-6">
              <div className="text-center space-y-3">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center mx-auto shadow-md shadow-blue-500/20">
                  <Bot className="h-6 w-6" />
                </div>
                <h2 className="text-xl font-bold text-slate-900">
                  Enterprise Documentation Assistant
                </h2>
                <p className="text-xs text-slate-500 max-w-lg mx-auto leading-relaxed">
                  Ask natural-language questions grounded in uploaded organization manuals, policies, and API specifications. All answers feature verifiable citations.
                </p>
              </div>

              {/* Prompt Suggestions */}
              <div className="space-y-2.5">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">
                  Recommended Test Inquiries
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setInputQuery(q.text)}
                      className="text-left p-3.5 bg-white rounded-xl border border-slate-200/80 hover:border-blue-500 hover:shadow-xs transition text-xs group"
                    >
                      <div className="text-[10px] uppercase font-bold text-blue-600 font-mono mb-1">
                        {q.category}
                      </div>
                      <div className="text-slate-700 font-medium group-hover:text-slate-900 leading-snug">
                        "{q.text}"
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Message Bubbles */
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg, index) => {
                const isUser = msg.role === 'user';

                return (
                  <div
                    key={msg.id || index}
                    className={`flex items-start gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    {!isUser && (
                      <div className="h-8 w-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm shadow-blue-500/20 mt-1">
                        <Bot className="h-4 w-4" />
                      </div>
                    )}

                    <div className={`max-w-2xl ${isUser ? 'w-auto' : 'w-full'}`}>
                      {isUser ? (
                        <div className="bg-blue-600 text-white px-4 py-3 rounded-2xl rounded-tr-xs text-xs font-medium shadow-sm">
                          {msg.content}
                        </div>
                      ) : (
                        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-4">
                          {/* Top Meta Bar */}
                          <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
                            {getConfidenceBadge(msg.confidence, msg.confidence_score)}

                            {msg.retrieved_evidence && msg.retrieved_evidence.length > 0 && (
                              <button
                                onClick={() => onOpenEvidence(msg.retrieved_evidence)}
                                className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 transition"
                              >
                                <Layers className="h-3.5 w-3.5" />
                                <span>{msg.retrieved_evidence.length} Retrieved Passages</span>
                              </button>
                            )}
                          </div>

                          {/* Conflict Alert if applicable */}
                          {msg.conflict && (
                            <ConflictBanner conflict={msg.conflict} />
                          )}

                          {/* Formatted Content */}
                          <MarkdownView content={msg.content} />

                          {/* Clickable Citations */}
                          {msg.citations && msg.citations.length > 0 && (
                            <div className="pt-3 border-t border-slate-100 space-y-2">
                              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                                Verified Source Citations
                              </div>
                              <div className="flex flex-wrap gap-2">
                                {msg.citations.map((cit, citIdx) => (
                                  <button
                                    key={citIdx}
                                    onClick={() => onOpenEvidence(msg.retrieved_evidence, cit.chunk_id)}
                                    className="inline-flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-blue-50 hover:border-blue-300 border border-slate-200 text-slate-700 hover:text-blue-700 px-3 py-1.5 rounded-lg transition font-medium group"
                                  >
                                    <FileText className="h-3.5 w-3.5 text-blue-600" />
                                    <span>{cit.document_name}</span>
                                    {cit.page_number && (
                                      <span className="text-[10px] text-slate-400 group-hover:text-blue-500 font-mono">
                                        (p. {cit.page_number})
                                      </span>
                                    )}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Bottom Action Footer */}
                          <div className="pt-2 flex items-center justify-between text-slate-400 text-xs border-t border-slate-50">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleCopy(msg.content, msg.id)}
                                className="flex items-center gap-1 hover:text-slate-700 transition"
                                title="Copy answer"
                              >
                                <Copy className="h-3.5 w-3.5" />
                                <span>{feedbackState[msg.id] === 'copied' ? 'Copied!' : 'Copy'}</span>
                              </button>
                            </div>

                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => handleFeedback(msg.id, 'positive')}
                                className={`p-1 rounded hover:text-slate-700 ${feedbackState[msg.id] === 'positive' ? 'text-emerald-600' : ''}`}
                                title="Helpful"
                              >
                                <ThumbsUp className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => handleFeedback(msg.id, 'negative')}
                                className={`p-1 rounded hover:text-slate-700 ${feedbackState[msg.id] === 'negative' ? 'text-rose-600' : ''}`}
                                title="Not helpful"
                              >
                                <ThumbsDown className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {isUser && (
                      <div className="h-8 w-8 rounded-xl bg-slate-800 text-white flex items-center justify-center shrink-0 mt-1">
                        <User className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                );
              })}

              {isLoading && (
                <div className="flex items-start gap-4">
                  <div className="h-8 w-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-1 animate-pulse">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs flex items-center gap-3">
                    <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
                    <span className="text-xs text-slate-600 font-medium">
                      Retrieving evidence, assessing confidence, and synthesizing answer...
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Bottom Input Area */}
        <div className="p-4 bg-white border-t border-slate-200/80">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-2">
            <div className="relative flex items-center bg-slate-50 border border-slate-200 rounded-2xl focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition p-1.5">
              <textarea
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                rows={1}
                placeholder="Ask a question about organization policies, APIs, billing, authentication..."
                className="w-full px-3 py-2 text-xs bg-transparent border-0 focus:outline-none resize-none max-h-32 text-slate-800 placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isLoading}
                className="h-9 w-9 rounded-xl bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 shrink-0 transition"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <div className="text-[11px] text-slate-400 text-center">
              Evidence-First RAG: Answers are strictly generated from indexed documents. If insufficient evidence exists, the assistant abstains.
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
