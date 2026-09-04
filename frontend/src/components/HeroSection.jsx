import React, { useState, useEffect } from 'react';
import { Zap, ShieldCheck, ArrowRight, Activity, TrendingUp, Bell, Download } from 'lucide-react';

export default function HeroSection({ setActiveTab }) {
  const [tickerIndex, setTickerIndex] = useState(0);
  const tickerEvents = [
    { company: "FinTech Enterprise Inc.", event: "8 concurrent pricing page visits from HQ domain", score: 98, time: "Just now" },
    { company: "CloudScale Systems", event: "Installed intent webhook API & removed legacy tracking", score: 94, time: "2m ago" },
    { company: "HyperGrowth SaaS", event: "Appointed VP of RevOps & posted 6 SDR roles", score: 91, time: "4m ago" }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % tickerEvents.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto overflow-hidden">
      {/* Background Subtle Gradient Blobs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-blue-600/15 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[400px] h-[250px] bg-amber-500/10 blur-[100px] rounded-full pointer-events-none" />

      <div className="relative z-10 text-center max-w-4xl mx-auto">
        {/* Live Signal Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-slate-300 text-xs font-semibold mb-6 shadow-xl">
          <span className="pulse-dot"></span>
          <span className="text-blue-400 font-bold uppercase tracking-wider">Real-Time Firehose Active</span>
          <span className="text-slate-600">|</span>
          <span className="text-amber-400">Micro-Signals. Macro-Revenue.</span>
        </div>

        {/* Primary Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.15] mb-6">
          Intent Happens Fast. <br className="hidden sm:block" />
          <span className="bg-gradient-to-r from-blue-400 via-sky-300 to-amber-400 bg-clip-text text-transparent">
            QUANTA Happens First.
          </span>
        </h1>

        {/* Human-Written Copy */}
        <p className="text-lg sm:text-xl text-slate-300 font-normal leading-relaxed max-w-3xl mx-auto mb-10">
          Stop chasing cold lead lists or waiting for buyers to fill out contact forms on your competitors’ websites. 
          QUANTA captures sub-second behavioral micro-signals across the web, scores intent instantly, and feeds revenue-ready accounts straight to your team.
        </p>

        {/* Primary CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
          <button 
            onClick={() => {
              document.getElementById('lead-form-section')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="btn-primary text-base px-8 py-3.5 w-full sm:w-auto"
          >
            <span>Book a Demo</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          <button 
            onClick={() => setActiveTab('signals')}
            className="btn-secondary text-base px-6 py-3.5 w-full sm:w-auto flex items-center justify-center gap-2"
          >
            <Activity className="w-5 h-5 text-blue-400" />
            <span>Explore Live Stream</span>
          </button>
          <a 
            href="/extension/quanta-extension.zip"
            download="quanta-extension.zip"
            className="btn-secondary text-base px-6 py-3.5 w-full sm:w-auto flex items-center justify-center gap-2"
          >
            <Download className="w-5 h-5 text-amber-400" />
            <span>Chrome Extension (Mac ZIP)</span>
          </a>
        </div>

        {/* Ticker Simulation Card */}
        <div className="card-dark p-4 sm:p-5 max-w-2xl mx-auto text-left border-slate-800 shadow-2xl relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-3 border-b border-slate-800/80 pb-2">
            <span className="flex items-center gap-1.5 text-blue-400 font-semibold uppercase tracking-wider">
              <Bell className="w-3.5 h-3.5 text-amber-400 animate-bounce" /> Live Intent Intercept
            </span>
            <span className="text-slate-500 font-mono">Stream ID: QN-89302</span>
          </div>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-white mb-1">
                {tickerEvents[tickerIndex].company}
              </h4>
              <p className="text-xs text-slate-300">
                {tickerEvents[tickerIndex].event}
              </p>
            </div>
            <div className="text-right shrink-0">
              <span className="badge-gold">
                Score: {tickerEvents[tickerIndex].score}/100
              </span>
              <div className="text-[10px] text-slate-500 mt-1">
                {tickerEvents[tickerIndex].time}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
