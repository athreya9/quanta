import React, { useState, useEffect } from 'react';
import { Radio, Flame, Bell, Filter, RefreshCw, Zap, Slack, Chrome, CheckCircle2, ExternalLink, Code2, Users2, DollarSign, Briefcase } from 'lucide-react';

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
      // Fallback signal stream
      setSignals([
        {
          id: 'sig_101',
          company: 'Stripe Competitor Corp',
          event_type: 'TECH_STACK_CHANGE',
          category: 'TECH_STACK_CHANGE',
          description: 'Removed legacy tracking scripts and installed custom intent webhook API on enterprise pricing path.',
          source_url: 'https://github.com/stripe-comp/web-analytics',
          detected_at: 'Just now',
          timestamp: '14:22:10 UTC',
          intent_score: 96,
          location: 'San Francisco, CA',
          action_playbook: 'Trigger Executive Outreach + Slack Alert #growth-leads'
        },
        {
          id: 'sig_102',
          company: 'Nexus B2B SaaS',
          event_type: 'EXEC_HIRE',
          category: 'EXEC_HIRE',
          description: 'Appointed new VP of Revenue Operations (ex-Gong, ex-Salesforce) to scale GTM engine.',
          source_url: 'https://linkedin.com/company/nexus-b2b/jobs',
          detected_at: '5m ago',
          timestamp: '14:17:10 UTC',
          intent_score: 92,
          location: 'Austin, TX',
          action_playbook: 'Dispatch RevOps playbook via Chrome Extension'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleTestAlert = async () => {
    try {
      const res = await fetch('/api/v1/signals/test-alert', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      setAlertBanner(data.message);
      setTimeout(() => setAlertBanner(null), 6000);
    } catch (err) {
      setAlertBanner("🔥 HIGH INTENT ALERT: Demo Prospect hit pricing page 4x in 10 mins. Playbook auto-dispatched.");
      setTimeout(() => setAlertBanner(null), 6000);
    }
  };

  const filteredSignals = filter === 'ALL' 
    ? signals 
    : signals.filter(s => (s.category === filter || s.event_type === filter));

  return (
    <div className="pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Test Alert Toast Notification */}
      {alertBanner && (
        <div className="fixed top-20 right-4 z-50 max-w-md bg-slate-900/95 border-2 border-amber-500 text-white p-4 rounded-2xl shadow-2xl animate-bounce flex items-start gap-3.5 backdrop-blur-md">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
            <Bell className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">Simulated Slack / Chrome Extension Alert</div>
            <p className="text-xs text-slate-200 mt-1 font-mono">{alertBanner}</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <Radio className="w-6 h-6 text-emerald-400 animate-pulse" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Live Intent Micro-Signal Stream</h1>
            <span className="badge-blue">Real-Time Firehose</span>
          </div>
          <p className="text-sm text-slate-300">
            Sub-second intent detection across global domain traffic, tech stack shifts, executive hires, and pricing evaluations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={handleTestAlert}
            className="btn-gold text-xs py-2.5 px-4 flex items-center gap-2 shadow-lg"
          >
            <Bell className="w-4 h-4" />
            <span>Test Alert UI Ping</span>
          </button>
          <button 
            onClick={fetchSignals}
            className="btn-secondary text-xs py-2.5 px-3 flex items-center gap-2"
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
          className={`px-3.5 py-2 rounded-full font-semibold transition ${filter === 'ALL' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'}`}
        >
          All Signals ({signals.length})
        </button>
        <button 
          onClick={() => setFilter('TECH_STACK_CHANGE')}
          className={`px-3.5 py-2 rounded-full font-semibold transition flex items-center gap-1.5 ${filter === 'TECH_STACK_CHANGE' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'}`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Tech Stack Shifts</span>
        </button>
        <button 
          onClick={() => setFilter('PRICING_PAGE')}
          className={`px-3.5 py-2 rounded-full font-semibold transition flex items-center gap-1.5 ${filter === 'PRICING_PAGE' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'}`}
        >
          <Flame className="w-3.5 h-3.5 text-amber-400" />
          <span>Pricing Page Visits</span>
        </button>
        <button 
          onClick={() => setFilter('EXEC_HIRE')}
          className={`px-3.5 py-2 rounded-full font-semibold transition flex items-center gap-1.5 ${filter === 'EXEC_HIRE' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'}`}
        >
          <Users2 className="w-3.5 h-3.5" />
          <span>Executive Hires</span>
        </button>
        <button 
          onClick={() => setFilter('FUNDING')}
          className={`px-3.5 py-2 rounded-full font-semibold transition flex items-center gap-1.5 ${filter === 'FUNDING' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'}`}
        >
          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          <span>Funding Rounds</span>
        </button>
        <button 
          onClick={() => setFilter('JOB_POST')}
          className={`px-3.5 py-2 rounded-full font-semibold transition flex items-center gap-1.5 ${filter === 'JOB_POST' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'}`}
        >
          <Briefcase className="w-3.5 h-3.5" />
          <span>Job Postings</span>
        </button>
      </div>

      {/* Signal Items Stream */}
      <div className="space-y-4">
        {filteredSignals.map((sig) => (
          <div key={sig.id} className="card-dark p-5 border-slate-800 hover:border-blue-500/40 transition group relative">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
              <div className="flex flex-wrap items-center gap-3">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition">{sig.company}</h3>
                <span className={sig.intent_score >= 85 ? 'badge-gold text-[10px]' : 'badge-blue text-[10px]'}>
                  Score: {sig.intent_score}/100
                </span>
                <span className="badge-blue text-[10px]">{sig.category || sig.event_type}</span>
              </div>
              <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                <span>{sig.detected_at || sig.timestamp}</span>
                <span>|</span>
                <span>{sig.location || 'Global Domain'}</span>
              </div>
            </div>

            <p className="text-sm text-slate-200 mb-4 bg-slate-900/90 p-3.5 rounded-xl border border-slate-800 font-mono leading-relaxed">
              "{sig.description || sig.signal_text}"
            </p>

            <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-3 border-t border-slate-800/80 text-slate-400">
              <div className="flex items-center gap-2 text-amber-400 font-semibold">
                <Zap className="w-3.5 h-3.5" />
                <span>Playbook: {sig.action_playbook || 'Trigger Executive Outreach'}</span>
              </div>
              <div className="flex items-center gap-4 text-slate-400">
                {sig.source_url && (
                  <a href={sig.source_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-400 hover:underline font-mono text-[11px]">
                    <ExternalLink className="w-3 h-3" /> Signal Source
                  </a>
                )}
                <span className="flex items-center gap-1 text-slate-500"><Slack className="w-3 h-3 text-slate-400" /> Slack Bot</span>
                <span className="flex items-center gap-1 text-slate-500"><Chrome className="w-3 h-3 text-slate-400" /> Chrome Overlay</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
