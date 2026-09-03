import React from 'react';
import { Activity, Shield, ArrowRight, LayoutDashboard, Radio } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <header className="glass-nav fixed top-0 left-0 right-0 z-50 px-4 lg:px-8 py-3.5 flex items-center justify-between">
      {/* Brand Logo & Tagline */}
      <div 
        className="flex items-center gap-3 cursor-pointer" 
        onClick={() => setActiveTab('landing')}
      >
        <img 
          src="/quanta_logo.svg" 
          alt="QUANTA Logo" 
          className="h-9 w-auto" 
        />
      </div>

      {/* Desktop Navigation Links */}
      <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
        <button 
          onClick={() => setActiveTab('landing')} 
          className={`hover:text-white transition ${activeTab === 'landing' ? 'text-blue-400 font-semibold' : ''}`}
        >
          Engine Overview
        </button>
        <button 
          onClick={() => setActiveTab('signals')} 
          className={`hover:text-white flex items-center gap-1.5 transition ${activeTab === 'signals' ? 'text-blue-400 font-semibold' : ''}`}
        >
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          Live Micro-Signals
        </button>
        <button 
          onClick={() => setActiveTab('crm')} 
          className={`hover:text-white flex items-center gap-1.5 transition ${activeTab === 'crm' ? 'text-blue-400 font-semibold' : ''}`}
        >
          <LayoutDashboard className="w-4 h-4 text-amber-400" />
          QUANTA CRM
        </button>
        <a href="#faq" onClick={() => setActiveTab('landing')} className="hover:text-white transition">
          B2B FAQs
        </a>
      </nav>

      {/* CTA Buttons */}
      <div className="flex items-center gap-3">
        <button 
          onClick={() => {
            setActiveTab('landing');
            setTimeout(() => {
              document.getElementById('lead-form-section')?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
          }} 
          className="btn-primary text-xs sm:text-sm py-2 px-4"
        >
          <span>Get Signals</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
