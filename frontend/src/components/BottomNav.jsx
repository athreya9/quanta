import React from 'react';
import { Home, Layers, LayoutDashboard, Radio } from 'lucide-react';

export default function BottomNav({ activeTab, setActiveTab }) {
  return (
    <nav className="bottom-nav md:hidden">
      <button
        onClick={() => setActiveTab('landing')}
        className={`bottom-nav-item ${activeTab === 'landing' ? 'active' : ''}`}
      >
        <Home className="w-5 h-5" />
        <span>Home</span>
      </button>

      <button
        onClick={() => setActiveTab('pipeline')}
        className={`bottom-nav-item ${activeTab === 'pipeline' ? 'active' : ''}`}
      >
        <Layers className="w-5 h-5" />
        <span>Pipeline</span>
      </button>

      <button
        onClick={() => setActiveTab('signals')}
        className={`bottom-nav-item ${activeTab === 'signals' ? 'active' : ''}`}
      >
        <Radio className="w-5 h-5" />
        <span>Signals</span>
      </button>

      <button
        onClick={() => setActiveTab('crm')}
        className={`bottom-nav-item ${activeTab === 'crm' ? 'active' : ''}`}
      >
        <LayoutDashboard className="w-5 h-5" />
        <span>CRM</span>
      </button>
    </nav>
  );
}
