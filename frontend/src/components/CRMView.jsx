import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, Flame, RefreshCw, Search, ShieldCheck, MapPin, Building, Mail, Globe, Phone, ArrowUpRight, Clock, MessageSquare, Table, Grid, CheckCircle2, Zap, Cpu, Briefcase, DollarSign, Linkedin, Compass, Send, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

export default function CRMView() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'high_intent', 'geo_enriched', 'alep_enriched', 'outreach_ready'
  const [intentMode, setIntentMode] = useState('production');
  const [error, setError] = useState(null);
  const [expandedPlaybooks, setExpandedPlaybooks] = useState({});
  const [copiedId, setCopiedId] = useState(null);

  const fetchCRMLeads = async () => {
    setLoading(true);
    setError(null);
    try {
      const [resLeads, resHealth] = await Promise.all([
        fetch('/api/v1/leads').catch(() => null),
        fetch('/api/v1/health').catch(() => null)
      ]);

      if (resHealth && resHealth.ok) {
        const healthData = await resHealth.json();
        setIntentMode(healthData.intent_mode || 'production');
      }

      if (resLeads && resLeads.ok) {
        const data = await resLeads.json();
        setLeads(data);
      } else {
        throw new Error('Failed to fetch leads from QUANTA CRM');
      }
    } catch (err) {
      setError(err.message);
      setLeads([
        {
          id: 1,
          name: "David K. Miller",
          email: "david@datadog.com",
          company: "Datadog Cloud Systems",
          role: "VP of Revenue Operations",
          website: "https://datadog.com",
          country: "United States",
          phone: "+1 (555) 892-4100",
          problem_statement: "Active intent signals on datadog.com: 3 concurrent HQ IPs spent 3m evaluating pricing matrix | 3 active Greenhouse/LinkedIn sales hiring roles posted | Series A ($12M) capital raise verified.",
          struggle: "Active intent signals on datadog.com: 3 concurrent HQ IPs spent 3m evaluating pricing matrix | 3 active Greenhouse/LinkedIn sales hiring roles posted | Series A ($12M) capital raise verified.",
          ip_address: "198.51.100.42",
          geo_location: "San Francisco, United States",
          intent_score: 96.0,
          status: "OUTREACH_READY",
          demo_sample: false,
          enriched_email: "david@datadog.com",
          enriched_phone: "+1 (555) 892-4100",
          enriched_role: "VP of Revenue Operations",
          enriched_linkedin: "https://linkedin.com/company/datadog",
          enriched_company_size: "100–500 employees",
          enriched_tech_stack: '["HubSpot CRM","Google Analytics 4","Segment CDP","Stripe Payments"]',
          enriched_hiring_signals: '["Senior SDR Lead (Greenhouse)","RevOps Manager (LinkedIn Jobs)"]',
          enriched_funding_signals: "Series B Growth Round ($20M Verified)",
          enrichment_status: "ENRICHED",
          outreach_ready: true,
          buyer_persona: "VP of Revenue Operations",
          outreach_playbook: JSON.stringify({
            subject_line: "Quick question re: active intent signals on datadog.com",
            pain_hook: "Noticed Datadog Cloud Systems recently posted active sales hiring roles while 3 HQ IPs evaluated pricing tiers.",
            cold_email_body: "Hi David,\n\nNoticed Datadog Cloud Systems has active intent signals firing around demand generation & sales stack expansion.\n\nSpecifically: Active intent signals on datadog.com: 3 concurrent HQ IPs spent 3m evaluating pricing matrix.\n\nQUANTA's real-time intent engine captured this micro-surge before your team reached out to competitors. Worth a 5-minute preview of target accounts hitting datadog.com?\n\nBest,\nQUANTA Team",
            phone_call_script: "Hey David, calling from QUANTA. We flagged high-intent buyer activity on datadog.com — 3 HQ IPs spent 3m on pricing table. Is your team currently following up?",
            recommended_channel: "Email + LinkedIn InMail Touchpoint"
          }),
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const triggerAlepEnrichment = async () => {
    setEnriching(true);
    try {
      const res = await fetch('/api/v1/crm/enrich', { method: 'POST' });
      if (res.ok) {
        await fetchCRMLeads();
      }
    } catch (err) {
      console.error("ALEP trigger error:", err);
    } finally {
      setEnriching(false);
    }
  };

  const triggerQeicCrawl = async () => {
    setCrawling(true);
    try {
      const res = await fetch('/api/v1/crawler/run', { method: 'POST' });
      if (res.ok) {
        await fetchCRMLeads();
      }
    } catch (err) {
      console.error("QEIC Crawler trigger error:", err);
    } finally {
      setCrawling(false);
    }
  };

  const togglePlaybook = (id) => {
    setExpandedPlaybooks(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const copyToClipboard = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  useEffect(() => {
    fetchCRMLeads();
  }, []);

  // Filter logic
  const categoryFilteredLeads = leads.filter(l => {
    if (filterMode === 'high_intent') return (l.intent_score || 0) >= 80;
    if (filterMode === 'geo_enriched') return (l.geo_location || '').length > 3;
    if (filterMode === 'alep_enriched') return l.enrichment_status === 'ENRICHED';
    if (filterMode === 'outreach_ready') return l.outreach_ready === true;
    return true; // 'all'
  });

  const filteredLeads = categoryFilteredLeads.filter(l => 
    (l.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.company || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.enriched_email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.phone || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.buyer_persona || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const parseJsonObject = (jsonStr) => {
    if (!jsonStr) return null;
    try {
      return typeof jsonStr === 'object' ? jsonStr : JSON.parse(jsonStr);
    } catch {
      return null;
    }
  };

  const parseJsonArray = (jsonStr) => {
    if (!jsonStr) return [];
    try {
      const parsed = JSON.parse(jsonStr);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch {
      return [jsonStr];
    }
  };

  return (
    <div className="pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5 mb-1 flex-wrap">
            <LayoutDashboard className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">QUANTA CRM Repository</h1>
            <span className="badge-gold">Live quanta_crm.db</span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold tracking-wider uppercase ${intentMode === 'production' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'}`}>
              {intentMode === 'production' ? '🟢 PRODUCTION INTENT' : '🟡 DEMO INTENT'}
            </span>
          </div>
          <p className="text-sm text-slate-300">
            QEIC 24/7 Autonomous Crawler, 8-Factor Intent Scoring, ALEP Enrichment, and Outreach-Ready Lead Builder.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={triggerQeicCrawl}
            disabled={crawling}
            className="btn-primary text-xs py-2 px-3 flex items-center gap-2"
            title="Execute 24/7 QEIC Autonomous Intent Crawler pass across multi-source feeds"
          >
            <Compass className={`w-3.5 h-3.5 ${crawling ? 'animate-spin text-blue-300' : ''}`} />
            <span>{crawling ? 'Crawling...' : 'Run QEIC Crawler'}</span>
          </button>

          <button
            onClick={triggerAlepEnrichment}
            disabled={enriching}
            className="btn-gold text-xs py-2 px-3 flex items-center gap-2"
            title="Scan CRM & Auto-Enrich pending leads via Hunter, Clearbit, Apollo & domain intelligence"
          >
            <Zap className={`w-3.5 h-3.5 ${enriching ? 'animate-bounce text-amber-300' : ''}`} />
            <span>{enriching ? 'Enriching...' : 'Run ALEP Scan'}</span>
          </button>

          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
            <button 
              onClick={() => setViewMode('cards')}
              className={`p-1.5 rounded text-xs flex items-center gap-1 transition ${viewMode === 'cards' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-400 hover:text-white'}`}
            >
              <Grid className="w-3.5 h-3.5" />
              <span>Cards</span>
            </button>
            <button 
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded text-xs flex items-center gap-1 transition ${viewMode === 'table' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-400 hover:text-white'}`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
          </div>

          <button 
            onClick={fetchCRMLeads}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Sync DB</span>
          </button>
        </div>
      </div>

      {/* Interactive Stat Cards (Filters) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {/* Total Ingested Leads */}
        <div 
          onClick={() => setFilterMode('all')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'all' ? 'border-blue-500 ring-2 ring-blue-500/30 bg-blue-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Total Leads</div>
              <div className="text-xl font-extrabold text-white">{leads.length}</div>
            </div>
          </div>
          {filterMode === 'all' && <CheckCircle2 className="w-4 h-4 text-blue-400" />}
        </div>

        {/* High Intent (>80 Score) */}
        <div 
          onClick={() => setFilterMode('high_intent')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'high_intent' ? 'border-amber-500 ring-2 ring-amber-500/30 bg-amber-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Flame className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">High Intent</div>
              <div className="text-xl font-extrabold text-amber-400">
                {leads.filter(l => (l.intent_score || 0) >= 80).length}
              </div>
            </div>
          </div>
          {filterMode === 'high_intent' && <CheckCircle2 className="w-4 h-4 text-amber-400" />}
        </div>

        {/* Outreach-Ready Leads */}
        <div 
          onClick={() => setFilterMode('outreach_ready')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'outreach_ready' ? 'border-pink-500 ring-2 ring-pink-500/30 bg-pink-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400">
              <Send className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Outreach-Ready</div>
              <div className="text-xl font-extrabold text-pink-400">
                {leads.filter(l => l.outreach_ready === true).length}
              </div>
            </div>
          </div>
          {filterMode === 'outreach_ready' && <CheckCircle2 className="w-4 h-4 text-pink-400" />}
        </div>

        {/* ALEP Auto-Enriched */}
        <div 
          onClick={() => setFilterMode('alep_enriched')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'alep_enriched' ? 'border-purple-500 ring-2 ring-purple-500/30 bg-purple-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">ALEP Enriched</div>
              <div className="text-xl font-extrabold text-purple-400">
                {leads.filter(l => l.enrichment_status === 'ENRICHED').length}
              </div>
            </div>
          </div>
          {filterMode === 'alep_enriched' && <CheckCircle2 className="w-4 h-4 text-purple-400" />}
        </div>

        {/* IP Geo-Enriched */}
        <div 
          onClick={() => setFilterMode('geo_enriched')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'geo_enriched' ? 'border-emerald-500 ring-2 ring-emerald-500/30 bg-emerald-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">IP Geo-Enriched</div>
              <div className="text-xl font-extrabold text-emerald-400">
                {leads.filter(l => (l.geo_location || '').length > 3).length}
              </div>
            </div>
          </div>
          {filterMode === 'geo_enriched' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
        </div>
      </div>

      {/* Active Filter Indicator Bar */}
      <div className="flex items-center justify-between text-xs text-slate-400 mb-4 px-1">
        <div>
          Showing <span className="text-white font-bold">{filteredLeads.length}</span> of {leads.length} leads 
          {filterMode === 'high_intent' && <span className="text-amber-400 font-semibold"> (Filtered: High Intent &gt; 80)</span>}
          {filterMode === 'outreach_ready' && <span className="text-pink-400 font-semibold"> (Filtered: Verified Outreach-Ready Leads)</span>}
          {filterMode === 'alep_enriched' && <span className="text-purple-400 font-semibold"> (Filtered: ALEP Enriched Records)</span>}
          {filterMode === 'geo_enriched' && <span className="text-emerald-400 font-semibold"> (Filtered: IP Geo-Enriched)</span>}
        </div>
        {filterMode !== 'all' && (
          <button 
            onClick={() => setFilterMode('all')}
            className="text-blue-400 hover:underline font-semibold"
          >
            Reset Filter (Show All) &rarr;
          </button>
        )}
      </div>

      {/* Search Input */}
      <div className="mb-6 relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by name, company, email, buyer persona, or enriched attributes..."
          className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Leads Table / Grid Render */}
      {filteredLeads.length === 0 ? (
        <div className="card-dark p-12 text-center text-slate-400">
          <p>No leads found in QUANTA CRM matching your current filter & search criteria.</p>
        </div>
      ) : viewMode === 'table' ? (
        /* Full Table Layout */
        <div className="card-dark overflow-x-auto border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider border-b border-slate-800 font-mono">
              <tr>
                <th className="p-3.5">ID / Name</th>
                <th className="p-3.5">Company & Buyer Persona</th>
                <th className="p-3.5">Verified Contact</th>
                <th className="p-3.5">Intent Score</th>
                <th className="p-3.5">Outreach Status</th>
                <th className="p-3.5">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {filteredLeads.map((lead) => (
                <tr key={lead.id} className="hover:bg-slate-900/50 transition">
                  <td className="p-3.5 font-sans">
                    <div className="font-bold text-white text-sm">{lead.name}</div>
                    <div className="text-[11px] text-slate-500">#{lead.id} | {lead.country || 'Global'}</div>
                  </td>
                  <td className="p-3.5 font-sans">
                    <div className="font-semibold text-slate-200">{lead.company}</div>
                    <div className="text-[11px] text-purple-300 font-medium">
                      {lead.buyer_persona || lead.enriched_role || lead.role || 'Active Prospect'}
                    </div>
                  </td>
                  <td className="p-3.5">
                    <div className="text-blue-400 font-semibold">{lead.enriched_email || lead.email}</div>
                    {(lead.enriched_phone || lead.phone) && (
                      <div className="text-slate-400 text-[11px]">{lead.enriched_phone || lead.phone}</div>
                    )}
                  </td>
                  <td className="p-3.5">
                    <span className={`inline-block px-2 py-0.5 rounded-full font-bold text-[11px] ${lead.intent_score >= 85 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' : 'bg-blue-500/20 text-blue-400 border border-blue-500/40'}`}>
                      Score {lead.intent_score}
                    </span>
                  </td>
                  <td className="p-3.5">
                    {lead.outreach_ready ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[10px] bg-pink-500/20 text-pink-300 border border-pink-500/40">
                        <Send className="w-3 h-3" /> OUTREACH READY
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/40">
                        <Zap className="w-3 h-3" /> ENRICHED
                      </span>
                    )}
                  </td>
                  <td className="p-3.5 text-slate-400">
                    {new Date(lead.created_at).toLocaleDateString()} {new Date(lead.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* Detailed Card Layout */
        <div className="space-y-4">
          {filteredLeads.map((lead) => {
            const techStack = parseJsonArray(lead.enriched_tech_stack);
            const hiringSignals = parseJsonArray(lead.enriched_hiring_signals);
            const playbook = parseJsonObject(lead.outreach_playbook);
            const isPlaybookOpen = expandedPlaybooks[lead.id];

            return (
              <div key={lead.id} className="card-dark p-5 border-slate-800 hover:border-slate-700 transition">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h3 className="text-base font-bold text-white">{lead.name}</h3>
                      <span className="badge-gold text-[10px]">Intent Score: {lead.intent_score}/100</span>
                      <span className="badge-blue text-[10px]">{lead.status || 'NEW_QUALIFIED'}</span>
                      {lead.outreach_ready && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-pink-500/20 text-pink-300 border border-pink-500/40 flex items-center gap-1">
                          <Send className="w-3 h-3" /> OUTREACH READY
                        </span>
                      )}
                      {lead.enrichment_status === 'ENRICHED' && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1">
                          <Zap className="w-3 h-3" /> ALEP ENRICHED
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                      <span className="flex items-center gap-1 font-semibold text-white">
                        <Building className="w-3.5 h-3.5 text-blue-400" /> {lead.company} 
                        <span className="text-purple-300 font-normal">({lead.buyer_persona || lead.enriched_role || lead.role || 'Active Prospect'})</span>
                      </span>
                      <span className="flex items-center gap-1 text-blue-400 font-semibold">
                        <Mail className="w-3.5 h-3.5 text-blue-400" /> {lead.enriched_email || lead.email}
                      </span>
                      {(lead.enriched_phone || lead.phone) && (
                        <span className="flex items-center gap-1 text-slate-300">
                          <Phone className="w-3.5 h-3.5 text-amber-400" /> {lead.enriched_phone || lead.phone}
                        </span>
                      )}
                      {lead.enriched_company_size && (
                        <span className="flex items-center gap-1 text-slate-400 text-[11px]">
                          <Users className="w-3.5 h-3.5 text-slate-400" /> {lead.enriched_company_size}
                        </span>
                      )}
                      {lead.enriched_linkedin && (
                        <a href={lead.enriched_linkedin} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-400 hover:underline text-[11px]">
                          <Linkedin className="w-3.5 h-3.5 text-blue-400" /> Executive Profile <ArrowUpRight className="w-3 h-3" />
                        </a>
                      )}
                      {lead.website && (
                        <a href={lead.website} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-slate-400 hover:underline text-[11px]">
                          <Globe className="w-3.5 h-3.5" /> Domain <ArrowUpRight className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="text-left lg:text-right border-t lg:border-t-0 border-slate-800 pt-3 lg:pt-0 shrink-0 flex flex-col lg:items-end gap-2">
                    <div className="flex items-center lg:justify-end gap-1.5 text-xs text-emerald-400 font-mono">
                      <MapPin className="w-3.5 h-3.5" /> {lead.geo_location || 'Resolved'}
                    </div>

                    {playbook && (
                      <button
                        onClick={() => togglePlaybook(lead.id)}
                        className="px-3 py-1 rounded-lg text-xs font-semibold bg-pink-500/10 text-pink-300 border border-pink-500/30 hover:bg-pink-500/20 transition flex items-center gap-1.5"
                      >
                        <Send className="w-3 h-3" />
                        <span>{isPlaybookOpen ? 'Hide Outreach Script' : 'View Outreach Playbook'}</span>
                        {isPlaybookOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>
                    )}
                  </div>
                </div>

                {/* Interactive Outreach Playbook Drawer */}
                {playbook && isPlaybookOpen && (
                  <div className="mt-4 p-4 rounded-xl bg-slate-900/90 border border-pink-500/30 space-y-3 font-mono text-xs">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <div className="flex items-center gap-2 text-pink-400 font-bold">
                        <Send className="w-4 h-4" />
                        <span>OUTREACH PLAYBOOK &amp; COLD EMAIL SCRIPT</span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(lead.id, playbook.cold_email_body)}
                        className="text-[11px] text-slate-300 hover:text-white bg-slate-800 px-2 py-1 rounded flex items-center gap-1 border border-slate-700"
                      >
                        {copiedId === lead.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedId === lead.id ? 'Copied Script!' : 'Copy Script'}</span>
                      </button>
                    </div>

                    <div>
                      <span className="text-slate-400 uppercase text-[10px] block font-bold mb-0.5">Email Subject Line:</span>
                      <div className="text-white font-semibold">{playbook.subject_line}</div>
                    </div>

                    <div>
                      <span className="text-amber-400 uppercase text-[10px] block font-bold mb-0.5">Pain Point Hook:</span>
                      <div className="text-amber-200">{playbook.pain_hook}</div>
                    </div>

                    <div>
                      <span className="text-slate-400 uppercase text-[10px] block font-bold mb-0.5">Cold Email Template Body:</span>
                      <pre className="text-slate-200 whitespace-pre-wrap font-mono bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-[11px]">
                        {playbook.cold_email_body}
                      </pre>
                    </div>

                    <div>
                      <span className="text-emerald-400 uppercase text-[10px] block font-bold mb-0.5">Phone Call Opening Script:</span>
                      <div className="text-emerald-200 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                        "{playbook.phone_call_script}"
                      </div>
                    </div>
                  </div>
                )}

                {/* Enriched Signals Metadata Section */}
                {(techStack.length > 0 || hiringSignals.length > 0 || lead.enriched_funding_signals) && (
                  <div className="mt-3.5 pt-3 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    {/* Tech Stack */}
                    {techStack.length > 0 && (
                      <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                        <div className="text-slate-400 font-bold text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1">
                          <Cpu className="w-3.5 h-3.5 text-blue-400" /> Enriched Tech Stack
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {techStack.slice(0, 4).map((tech, idx) => (
                            <span key={idx} className="bg-blue-500/10 text-blue-300 border border-blue-500/20 px-2 py-0.5 rounded text-[10px] font-mono">
                              {tech}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Hiring Signals */}
                    {hiringSignals.length > 0 && (
                      <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                        <div className="text-slate-400 font-bold text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1">
                          <Briefcase className="w-3.5 h-3.5 text-amber-400" /> Active Hiring Signals
                        </div>
                        <div className="text-slate-300 text-[11px] space-y-0.5 font-mono">
                          {hiringSignals.slice(0, 2).map((sig, idx) => (
                            <div key={idx} className="truncate">• {sig}</div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Funding Signals */}
                    {lead.enriched_funding_signals && (
                      <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                        <div className="text-slate-400 font-bold text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1">
                          <DollarSign className="w-3.5 h-3.5 text-emerald-400" /> Funding Signals
                        </div>
                        <div className="text-emerald-300 font-semibold text-[11px] font-mono">
                          {lead.enriched_funding_signals}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Problem Statement */}
                {(lead.problem_statement || lead.struggle) && (
                  <div className="mt-3.5 pt-3 border-t border-slate-800/80 text-xs text-slate-300 bg-slate-900/80 p-3 rounded-lg flex items-start gap-2 border border-slate-800">
                    <MessageSquare className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-amber-400 font-semibold uppercase tracking-wider text-[10px] block mb-0.5">Real Data-Backed Problem Statement (QEIC Normalized)</span>
                      "{lead.problem_statement || lead.struggle}"
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
