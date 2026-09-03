import React from 'react';
import { Home, Radio, LayoutDashboard, Settings } from 'lucide-react';

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

      <button 
        onClick={() => {
          alert("QUANTA Settings & API Credentials configured for Port 3002 backend.");
        }}
        className="bottom-nav-item"
      >
        <Settings className="w-5 h-5" />
        <span>Settings</span>
      </button>
    </nav>
  );
}
