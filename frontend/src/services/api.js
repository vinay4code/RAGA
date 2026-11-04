const BASE_URL = '/api';

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${BASE_URL}/dashboard/stats`);
  if (!res.ok) throw new Error('Failed to fetch dashboard stats');
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${BASE_URL}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function fetchDocumentDetails(docId) {
  const res = await fetch(`${BASE_URL}/documents/${docId}`);
  if (!res.ok) throw new Error('Failed to fetch document details');
  return res.json();
}

export async function uploadDocuments(fileList) {
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append('files', fileList[i]);
  }
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${BASE_URL}/documents/${docId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
}

export async function sendChatMessage(question, conversationId = null, topK = 5, threshold = 0.35) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
      top_k: topK,
      relevance_threshold: threshold
    })
  });
  if (!res.ok) throw new Error('Chat request failed');
  return res.json();
}

export async function fetchConversations() {
  const res = await fetch(`${BASE_URL}/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function fetchConversationHistory(convId) {
  const res = await fetch(`${BASE_URL}/conversations/${convId}`);
  if (!res.ok) throw new Error('Failed to fetch conversation history');
  return res.json();
}

export async function fetchSourceChunk(chunkId) {
  const res = await fetch(`${BASE_URL}/sources/${chunkId}`);
  if (!res.ok) throw new Error('Failed to fetch source chunk');
  return res.json();
}

export async function runEvaluationSuite(datasetPath = null) {
  const res = await fetch(`${BASE_URL}/evaluation/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_path: datasetPath })
  });
  if (!res.ok) throw new Error('Evaluation failed to run');
  return res.json();
}

export async function fetchEvaluationResults() {
  const res = await fetch(`${BASE_URL}/evaluation/results`);
  if (!res.ok) throw new Error('Failed to fetch evaluation results');
  return res.json();
}
