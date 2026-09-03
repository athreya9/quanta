import React, { useState, useEffect } from 'react';
import { Radio, Flame, Bell, Filter, RefreshCw, Zap, Slack, Chrome, CheckCircle2 } from 'lucide-react';

export default function SignalFeed() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [alertBanner, setAlertBanner] = useState(null);

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/signals');
      if (res.ok) {
        const data = await res.json();
        setSignals(data);
      }
    } catch (err) {
      // Fallback signals
      setSignals([
        {
          id: 'sig_101',
          type: 'TECHNOGRAPHIC_SHIFT',
          company: 'Acme Financial Inc.',
          signal_text: 'Removed legacy web analytics and added pricing path intent listener.',
          timestamp: 'Just now',
          intent_score: 97,
          category: 'High Intent',
          location: 'San Francisco, CA',
          action_playbook: 'Trigger Executive Outreach + Slack Ping'
        },
        {
          id: 'sig_102',
          type: 'COMPETITOR_RESEARCH',
          company: 'HyperScale Cloud',
          signal_text: '12 concurrent IPs from corporate HQ evaluating enterprise pricing matrix.',
          timestamp: '3m ago',
          intent_score: 95,
          category: 'Evaluation',
          location: 'Austin, TX',
          action_playbook: 'Dispatch RevOps Playbook via Chrome Extension'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleTestAlert = async () => {
    try {
      const res = await fetch('/api/v1/signals/test-alert', { method: 'POST' });
      const data = await res.json();
      setAlertBanner(data.message);
      setTimeout(() => setAlertBanner(null), 5000);
    } catch (err) {
      setAlertBanner("🔥 HIGH INTENT ALERT: Demo Prospect hit pricing page 4x in 10 mins. Playbook auto-dispatched.");
      setTimeout(() => setAlertBanner(null), 5000);
    }
  };

  const filteredSignals = filter === 'ALL' 
    ? signals 
    : signals.filter(s => s.type === filter);

  return (
    <div className="pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Test Alert Banner Toast */}
      {alertBanner && (
        <div className="fixed top-20 right-4 z-50 max-w-md bg-slate-900 border-2 border-amber-500 text-white p-4 rounded-xl shadow-2xl animate-bounce flex items-start gap-3">
          <Bell className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">Simulated Slack / Chrome Ping</div>
            <p className="text-xs text-slate-200 mt-1">{alertBanner}</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <Radio className="w-6 h-6 text-emerald-400 animate-pulse" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Live Micro-Signal Stream</h1>
            <span className="badge-blue">Real-Time</span>
          </div>
          <p className="text-sm text-slate-300">
            Sub-second intent detection firehose across global domain traffic & technographic shifts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={handleTestAlert}
            className="btn-gold text-xs py-2 px-3 flex items-center gap-2"
          >
            <Bell className="w-4 h-4" />
            <span>Test Slack Alert Ping</span>
          </button>
          <button 
            onClick={fetchSignals}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-6 text-xs scrollbar-none">
        <button 
          onClick={() => setFilter('ALL')}
          className={`px-3 py-1.5 rounded-full font-semibold transition ${filter === 'ALL' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
        >
          All Signals
        </button>
        <button 
          onClick={() => setFilter('TECHNOGRAPHIC_SHIFT')}
          className={`px-3 py-1.5 rounded-full font-semibold transition ${filter === 'TECHNOGRAPHIC_SHIFT' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
        >
          Technographic
        </button>
        <button 
          onClick={() => setFilter('COMPETITOR_RESEARCH')}
          className={`px-3 py-1.5 rounded-full font-semibold transition ${filter === 'COMPETITOR_RESEARCH' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
        >
          Competitor Research
        </button>
        <button 
          onClick={() => setFilter('EXECUTIVE_HIRE')}
          className={`px-3 py-1.5 rounded-full font-semibold transition ${filter === 'EXECUTIVE_HIRE' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
        >
          Executive Hires
        </button>
      </div>

      {/* Signal Items List */}
      <div className="space-y-4">
        {filteredSignals.map((sig) => (
          <div key={sig.id} className="card-dark p-5 border-slate-800 hover:border-blue-500/40 transition group">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition">{sig.company}</h3>
                <span className="badge-gold text-[10px]">Score {sig.intent_score}</span>
                <span className="badge-blue text-[10px]">{sig.category}</span>
              </div>
              <div className="text-xs text-slate-400 font-mono">
                {sig.timestamp} | {sig.location}
              </div>
            </div>

            <p className="text-sm text-slate-200 mb-4 bg-slate-900/80 p-3 rounded-lg border border-slate-800 font-mono">
              "{sig.signal_text}"
            </p>

            <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-2 border-t border-slate-800/80 text-slate-400">
              <div className="flex items-center gap-2 text-amber-400 font-medium">
                <Zap className="w-3.5 h-3.5" />
                <span>Playbook: {sig.action_playbook}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-500">
                <span className="flex items-center gap-1"><Slack className="w-3 h-3 text-slate-400" /> Slack Bot</span>
                <span className="flex items-center gap-1"><Chrome className="w-3 h-3 text-slate-400" /> Chrome Overlay</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
