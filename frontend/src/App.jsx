import React, { useState } from 'react';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import SignalPipeline from './components/SignalPipeline';
import AudienceSection from './components/AudienceSection';
import LeadForm from './components/LeadForm';
import CRMView from './components/CRMView';
import SignalFeed from './components/SignalFeed';
import FAQSection from './components/FAQSection';
import AnalyticsTracker from './components/AnalyticsTracker';
import BottomNav from './components/BottomNav';
import LogoDownloader from './components/LogoDownloader';

export default function App() {
  const [activeTab, setActiveTab] = useState('landing');

  return (
    <div className="min-h-screen bg-[#0B1020] text-slate-100 font-sans selection:bg-blue-500 selection:text-white">
      <AnalyticsTracker />
      
      {/* Top Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main>
        {activeTab === 'landing' && (
          <>
            <HeroSection setActiveTab={setActiveTab} />
            <SignalPipeline />
            <AudienceSection />
            <LeadForm setActiveTab={setActiveTab} />
            <FAQSection />
            <LogoDownloader />
          </>
        )}

        {activeTab === 'signals' && (
          <SignalFeed />
        )}

        {activeTab === 'crm' && (
          <CRMView />
        )}
      </main>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-slate-800/80 bg-slate-950 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/quanta_logo.svg" alt="QUANTA" className="h-6 w-auto" />
            <span className="text-slate-500">|</span>
            <span className="text-slate-300">Micro-Signals. Macro-Revenue.</span>
          </div>

          <div className="text-slate-500">
            Domain: <span className="text-blue-400 font-mono">quanta.virtusol.com</span> (Port 3002)
          </div>

          <div className="text-slate-400">
            &copy; {new Date().getFullYear()} QUANTA Intent Engine. All rights reserved.
          </div>
        </div>
      </footer>

      {/* Sticky Bottom Nav on Mobile */}
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}
