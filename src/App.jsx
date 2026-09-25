import React, { useState } from 'react';
import Header from './components/Header';
import Workspace from './components/Workspace';
import EvaluationReport from './components/EvaluationReport';

export default function App() {
  const [activeTab, setActiveTab] = useState('workspace');

  return (
    <div className="min-h-screen bg-[#f8faf9] flex flex-col font-sans">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 pb-16">
        {activeTab === 'workspace' && <Workspace />}
        {activeTab === 'evaluation' && <EvaluationReport onClose={() => setActiveTab('workspace')} />}
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400 font-mono">
        redactly © 2026 • Private PII Redaction Workspace • All processing executed client-side
      </footer>
    </div>
  );
}
