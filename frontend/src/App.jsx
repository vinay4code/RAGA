import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import EvidenceDrawer from './components/EvidenceDrawer';
import DocumentModal from './components/DocumentModal';
import DashboardPage from './pages/DashboardPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import ChatPage from './pages/ChatPage';
import EvaluationPage from './pages/EvaluationPage';
import { fetchDashboardStats, fetchDocuments, fetchDocumentDetails } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [documents, setDocuments] = useState([]);
  
  // Evidence Drawer State
  const [evidenceDrawer, setEvidenceDrawer] = useState({
    isOpen: false,
    list: [],
    activeChunkId: null
  });

  // Document Details Modal State
  const [inspectDocData, setInspectDocData] = useState(null);
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);

  useEffect(() => {
    loadAppData();
  }, []);

  const loadAppData = async () => {
    try {
      const [statsData, docsData] = await Promise.all([
        fetchDashboardStats(),
        fetchDocuments()
      ]);
      setStats(statsData);
      setDocuments(docsData);
    } catch (err) {
      console.error('Error loading application data:', err);
    }
  };

  const handleOpenEvidence = (evidenceList, activeChunkId = null) => {
    setEvidenceDrawer({
      isOpen: true,
      list: evidenceList || [],
      activeChunkId: activeChunkId
    });
  };

  const handleCloseEvidence = () => {
    setEvidenceDrawer(prev => ({ ...prev, isOpen: false }));
  };

  const handleInspectDoc = async (docId) => {
    try {
      const details = await fetchDocumentDetails(docId);
      setInspectDocData(details);
      setIsDocModalOpen(true);
    } catch (err) {
      alert(`Could not load document details: ${err.message}`);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-800">
      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        stats={stats} 
      />

      {/* Main Dynamic Viewport */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'dashboard' && (
            <DashboardPage 
              stats={stats} 
              setActiveTab={setActiveTab} 
              onInspectDoc={handleInspectDoc} 
            />
          )}

          {activeTab === 'knowledge' && (
            <KnowledgeBasePage 
              documents={documents} 
              onRefresh={loadAppData} 
              onInspectDoc={handleInspectDoc} 
            />
          )}

          {activeTab === 'chat' && (
            <ChatPage 
              onOpenEvidence={handleOpenEvidence} 
              stats={stats} 
            />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationPage />
          )}
        </div>
      </main>

      {/* Right Evidence Passages Drawer */}
      <EvidenceDrawer 
        isOpen={evidenceDrawer.isOpen} 
        onClose={handleCloseEvidence} 
        evidenceList={evidenceDrawer.list} 
        activeChunkId={evidenceDrawer.activeChunkId} 
      />

      {/* Document Details / Chunks Modal */}
      <DocumentModal 
        isOpen={isDocModalOpen} 
        onClose={() => setIsDocModalOpen(false)} 
        docData={inspectDocData} 
      />
    </div>
  );
}
