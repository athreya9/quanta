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
        {/* Native Vector SVG Infinity Symbol (Zero raster background box, transparent) */}
        <svg 
          viewBox="0 0 160 80" 
          className="h-8 w-auto shrink-0 transition-transform group-hover:scale-105"
          style={{ background: 'transparent', mixBlendMode: 'normal' }}
          aria-label="QUANTA Infinity Symbol"
        >
          <defs>
            {/* Linear Gradient: Electric Blue/Cyan (#2563EB/#00F0FF) to Golden-Orange (#FF9900/#FFC700) */}
            <linearGradient id="quantaInfinityGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2563EB" />
              <stop offset="35%" stopColor="#00F0FF" />
              <stop offset="70%" stopColor="#FF9900" />
              <stop offset="100%" stopColor="#FFC700" />
            </linearGradient>
            <filter id="svgGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <path 
            d="M 80,40 C 100,16 128,16 140,40 C 152,64 128,64 80,40 C 52,16 28,16 20,40 C 8,64 32,64 80,40 Z"
            fill="none"
            stroke="url(#quantaInfinityGrad)"
            strokeWidth="13"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#svgGlow)"
          />
        </svg>
        
        {/* Preserved Brand Title & Subtext */}
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
