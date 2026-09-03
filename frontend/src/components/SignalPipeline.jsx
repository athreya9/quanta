import React from 'react';
import { Flame, Cpu, Slack, Chrome, ArrowRight, ShieldCheck, Zap } from 'lucide-react';

export default function SignalPipeline() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/60">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <span className="badge-blue mb-3">Architectural Blueprint</span>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          From Sub-Second Micro-Signals to Macro-Revenue
        </h2>
        <p className="text-slate-300 text-base sm:text-lg">
          QUANTA replaces traditional slow enrichment tools with an autonomous real-time engine built for high-velocity revenue teams.
        </p>
      </div>

      {/* 3 Steps Pipeline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
        {/* Step 1 */}
        <div className="card-dark p-6 sm:p-8 flex flex-col justify-between relative group">
          <div>
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform">
              <Flame className="w-6 h-6" />
            </div>
            <span className="text-xs font-mono text-blue-400 font-bold uppercase tracking-wider">Step 01</span>
            <h3 className="text-xl font-bold text-white mt-1 mb-3">Signal Firehose</h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-6">
              Continuous monitoring of domain-level intent, tech stack shifts, executive hiring surges, and competitor pricing evaluations across millions of nodes.
            </p>
          </div>
          <div className="border-t border-slate-800 pt-4 text-xs text-slate-400 flex items-center justify-between">
            <span>Latency: &lt;150ms</span>
            <span className="text-emerald-400 font-medium">100% Deterministic</span>
          </div>
        </div>

        {/* Step 2 */}
        <div className="card-dark p-6 sm:p-8 flex flex-col justify-between relative group">
          <div>
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-6 group-hover:scale-110 transition-transform">
              <Cpu className="w-6 h-6" />
            </div>
            <span className="text-xs font-mono text-amber-400 font-bold uppercase tracking-wider">Step 02</span>
            <h3 className="text-xl font-bold text-white mt-1 mb-3">AI Playbook Scoring</h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-6">
              Calculates real-time intent scores, enriches account decision-makers, and matches custom outbound playbooks tailored to the buyer's exact pain point.
            </p>
          </div>
          <div className="border-t border-slate-800 pt-4 text-xs text-slate-400 flex items-center justify-between">
            <span>Score Model: v4.2</span>
            <span className="text-amber-400 font-medium">Auto-Enriched</span>
          </div>
        </div>

        {/* Step 3 */}
        <div className="card-dark p-6 sm:p-8 flex flex-col justify-between relative group">
          <div>
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
              <Zap className="w-6 h-6" />
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider">Step 03</span>
            <h3 className="text-xl font-bold text-white mt-1 mb-3">Instant Delivery</h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-6">
              Instant alerts delivered directly to your reps via Slack bot, Chrome extension overlays, and seamless sync into QUANTA’s built-in CRM.
            </p>
          </div>
          <div className="border-t border-slate-800 pt-4 text-xs text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-2 text-slate-300">
              <Slack className="w-3.5 h-3.5" /> <Chrome className="w-3.5 h-3.5" /> Native
            </span>
            <span className="text-blue-400 font-medium">Zero Leakage</span>
          </div>
        </div>
      </div>
    </section>
  );
}
