import React from 'react';
import { Activity, Shield, ArrowRight, LayoutDashboard, Radio } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <header className="glass-nav fixed top-0 left-0 right-0 z-50 px-4 lg:px-8 py-3.5 flex items-center justify-between border-b border-slate-800/80">
      {/* Top-Left Branding Header */}
      <div 
        className="flex items-center gap-3 cursor-pointer select-none group" 
        onClick={() => setActiveTab('landing')}
      >
        <img 
          src="/quanta_icon.svg" 
          alt="QUANTA Infinity Brand Icon" 
          className="h-9 sm:h-10 w-auto drop-shadow-[0_0_16px_rgba(47,123,255,0.6)] transition-transform group-hover:scale-105" 
        />
        <div className="flex flex-col justify-center text-left">
          <div className="flex items-center gap-1.5 leading-none">
            <span className="text-lg sm:text-xl font-black tracking-wider text-white group-hover:text-blue-400 transition-colors">
              QUANTA
            </span>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <span className="text-xs text-slate-400 font-semibold tracking-[0.14em] group-hover:text-slate-300 transition-colors uppercase mt-0.5 leading-normal">
            REAL-TIME INTENT ENGINE
          </span>
        </div>
      </div>

      {/* Desktop Navigation Links (Vertically Centered) */}
      <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
        <button 
          onClick={() => setActiveTab('landing')} 
          className={`hover:text-white transition py-1 ${activeTab === 'landing' ? 'text-blue-400 font-semibold' : ''}`}
        >
          Engine Overview
        </button>
        <button 
          onClick={() => setActiveTab('signals')} 
          className={`hover:text-white flex items-center gap-1.5 transition py-1 ${activeTab === 'signals' ? 'text-blue-400 font-semibold' : ''}`}
        >
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          Live Micro-Signals
        </button>
        <button 
          onClick={() => setActiveTab('crm')} 
          className={`hover:text-white flex items-center gap-1.5 transition py-1 ${activeTab === 'crm' ? 'text-blue-400 font-semibold' : ''}`}
        >
          <LayoutDashboard className="w-4 h-4 text-amber-400" />
          QUANTA CRM
        </button>
        <a href="#faq" onClick={() => setActiveTab('landing')} className="hover:text-white transition py-1">
          B2B FAQs
        </a>
      </nav>

      {/* CTA Button (Vertically Centered) */}
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
