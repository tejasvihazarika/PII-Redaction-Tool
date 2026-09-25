import React from 'react';
import { ShieldCheck, BarChart3, Layers } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2.5 cursor-pointer" onClick={() => setActiveTab('workspace')}>
            <div className="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center text-emerald-400 shadow-sm border border-slate-800">
              <ShieldCheck className="w-5.5 h-5.5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900 font-sans">
              redactly
            </span>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('workspace')}
              className={`relative px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center space-x-2 ${
                activeTab === 'workspace'
                  ? 'text-slate-900 bg-slate-100/80 font-bold'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Workspace</span>
              {activeTab === 'workspace' && (
                <span className="absolute bottom-0 left-3 right-3 h-[2.5px] bg-emerald-600 rounded-full" />
              )}
            </button>

            <button
              onClick={() => setActiveTab('evaluation')}
              className={`relative px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center space-x-2 ${
                activeTab === 'evaluation'
                  ? 'text-slate-900 bg-slate-100/80 font-bold'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Evaluation report</span>
              {activeTab === 'evaluation' && (
                <span className="absolute bottom-0 left-3 right-3 h-[2.5px] bg-emerald-600 rounded-full" />
              )}
            </button>
          </nav>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center space-x-2 text-xs font-mono font-medium text-slate-600 bg-emerald-50/80 border border-emerald-200/60 px-3 py-1.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Engine online</span>
        </div>

      </div>
    </header>
  );
}
