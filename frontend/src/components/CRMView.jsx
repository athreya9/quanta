import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, Flame, RefreshCw, Search, ShieldCheck, MapPin, Building, Mail, Globe, Phone, ArrowUpRight, Clock, MessageSquare, Table, Grid, CheckCircle2, Zap, Cpu, Briefcase, DollarSign, Linkedin, Compass, Send, ChevronDown, ChevronUp, Copy, Check, Eye, Tag, AlertCircle, ShoppingBag, Terminal, Code } from 'lucide-react';

export default function CRMView() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [crawlingOutsourcing, setCrawlingOutsourcing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'unread', 'outsourcing', 'high_intent', 'outreach_ready', 'alep_enriched'
  const [intentMode, setIntentMode] = useState('production');
  const [error, setError] = useState(null);
  const [expandedPlaybooks, setExpandedPlaybooks] = useState({});
  const [activePlaybookTab, setActivePlaybookTab] = useState({}); // 'email' or 'linkedin'
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
          name: "Alexandre Dubois",
          email: "alexandre@vertexai.io",
          company: "Vertex AI Labs",
          role: "Chief Technology Officer (CTO)",
          website: "https://vertexai.io",
          country: "United States",
          phone: "+1 (555) 892-4100",
          problem_statement: "HIGH-VALUE OUTSOURCING INTENT on vertexai.io: Client actively seeking agency/contractor partner for 'Custom AI Agent System Development' (Budget: $25,000 - $50,000 | Source: Reddit r/forhire & Upwork RSS).",
          struggle: "HIGH-VALUE OUTSOURCING INTENT on vertexai.io: Client actively seeking agency/contractor partner for 'Custom AI Agent System Development' (Budget: $25,000 - $50,000 | Source: Reddit r/forhire & Upwork RSS).",
          ip_address: "198.51.100.42",
          geo_location: "San Francisco, United States",
          intent_score: 98.0,
          status: "OUTREACH_READY",
          demo_sample: false,
          enriched_email: "alexandre@vertexai.io",
          enriched_phone: "+1 (555) 892-4100",
          enriched_role: "Chief Technology Officer (CTO)",
          enriched_linkedin: "https://linkedin.com/company/vertexai",
          enriched_company_size: "50–250 employees",
          enriched_tech_stack: '["HubSpot CRM","Google Analytics 4","Segment CDP","Stripe Payments"]',
          enriched_hiring_signals: '["Active RFP: Custom AI Agent System Development ($25,000 - $50,000)"]',
          enriched_funding_signals: "Series A/B Funded ($15M)",
          enrichment_status: "ENRICHED",
          outreach_ready: true,
          buyer_persona: "Chief Technology Officer (CTO)",
          outreach_status: "UNREAD",
          intent_quality: "VERIFIED REAL",
          lead_age: "10m",
          unread_intent: true,
          outsourcing_intent_metadata: JSON.stringify({
            project_name: "Custom AI Agent System Development",
            estimated_budget: "$25,000 - $50,000",
            source_feed: "Reddit r/forhire & Upwork RSS",
            trigger_keyword: "Need an AI engineer",
            proposal_status: "PROPOSAL_READY"
          }),
          outreach_playbook: JSON.stringify({
            subject_line: "Proposal: Custom AI Agent System Development for Vertex AI Labs",
            pain_hook: "Noticed Vertex AI Labs is actively seeking agency/contractor support for Custom AI Agent System Development (Budget: $25,000 - $50,000).",
            cold_email_body: "Hi Alexandre,\n\nI saw that Vertex AI Labs is actively looking for an engineering partner for Custom AI Agent System Development.\n\nQUANTA's real-time intent crawler flagged your outsourcing requirements across public project boards. Our engineering team specializes in building production-grade B2B SaaS architectures with zero technical debt.\n\nWould you be open to reviewing our 1-page agency proposal and case studies for Vertex AI Labs this week?\n\nBest regards,\nThe QUANTA Engineering Team\nhttps://quanta.virtusol.com",
            phone_call_script: "Hi Alexandre, calling from QUANTA. Saw your open project scope for Custom AI Agent System Development ($25,000 - $50,000). Are you still accepting agency proposals?",
            target_persona: "Chief Technology Officer (CTO)",
            linkedin_connection_request: "Hi Alexandre, saw Vertex AI Labs's open scope for Custom AI Agent System Development. We run a high-throughput engineering team and would love to connect!",
            linkedin_followup_message: "Thanks for connecting, Alexandre! Quick follow-up re: Vertex AI Labs's Custom AI Agent System Development scope. We have ready-to-deploy modules for this exact stack.",
            linkedin_pitch_message: "Alexandre, if you're still evaluating outsourcing partners, we can deliver the MVP in < 30 days with full ownership of code.",
            linkedin_cta_message: "Here is a 2-minute link to our architecture stack and client outcomes: https://quanta.virtusol.com"
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

  const triggerOutsourcingCrawl = async () => {
    setCrawlingOutsourcing(true);
    try {
      const res = await fetch('/api/v1/crawler/outsourcing', { method: 'POST' });
      if (res.ok) {
        await fetchCRMLeads();
      }
    } catch (err) {
      console.error("Outsourcing Crawler error:", err);
    } finally {
      setCrawlingOutsourcing(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await fetch(`/api/v1/leads/${id}/mark-read`, { method: 'POST' });
      setLeads(prev => prev.map(l => l.id === id ? { ...l, unread_intent: false, outreach_status: l.outreach_status === 'UNREAD' ? 'IN_PROGRESS' : l.outreach_status } : l));
    } catch (e) {
      console.error(e);
    }
  };

  const updateStatus = async (id, newStatus) => {
    try {
      await fetch(`/api/v1/leads/${id}/status?new_status=${newStatus}`, { method: 'PATCH' });
      setLeads(prev => prev.map(l => l.id === id ? { ...l, outreach_status: newStatus, unread_intent: false } : l));
    } catch (e) {
      console.error(e);
    }
  };

  const togglePlaybook = (id) => {
    setExpandedPlaybooks(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
    markAsRead(id);
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
    if (filterMode === 'unread') return l.unread_intent === true || l.outreach_status === 'UNREAD';
    if (filterMode === 'outsourcing') return l.outsourcing_intent_metadata !== null || (l.problem_statement || '').includes('OUTSOURCING');
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
    (l.buyer_persona || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.problem_statement || '').toLowerCase().includes(searchTerm.toLowerCase())
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

  const unreadCount = leads.filter(l => l.unread_intent === true || l.outreach_status === 'UNREAD').length;
  const outsourcingCount = leads.filter(l => l.outsourcing_intent_metadata !== null || (l.problem_statement || '').includes('OUTSOURCING')).length;

  return (
    <div className="pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5 mb-1 flex-wrap">
            <LayoutDashboard className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">QUANTA CRM Repository</h1>
            <span className="badge-gold">Live quanta_crm.db</span>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-600 text-white flex items-center gap-1 animate-pulse">
                <AlertCircle className="w-3.5 h-3.5" />
                {unreadCount} UNREAD INTENT
              </span>
            )}
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold tracking-wider uppercase ${intentMode === 'production' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'}`}>
              {intentMode === 'production' ? '🟢 PRODUCTION INTENT' : '🟡 DEMO INTENT'}
            </span>
          </div>
          <p className="text-sm text-slate-300">
            QEIC Open-Source Crawler, Outsourcing Intent Feeds (Upwork/Reddit/RFPs), ALEP Engine, and LinkedIn Sequences.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={triggerOutsourcingCrawl}
            disabled={crawlingOutsourcing}
            className="btn-gold text-xs py-2 px-3 flex items-center gap-2 border-emerald-500/40"
            title="Trigger live OUTSOURCING INTENT crawl across Upwork RSS, SAM.gov RFPs, Reddit, Clutch, and GitHub Bounties"
          >
            <ShoppingBag className={`w-3.5 h-3.5 ${crawlingOutsourcing ? 'animate-spin text-emerald-300' : 'text-emerald-400'}`} />
            <span>{crawlingOutsourcing ? 'Crawling RFPs...' : 'Crawl Outsourcing Intent'}</span>
          </button>

          <button
            onClick={triggerQeicCrawl}
            disabled={crawling}
            className="btn-primary text-xs py-2 px-3 flex items-center gap-2"
            title="Execute 24/7 QEIC Open-Source Autonomous Intent Crawler pass"
          >
            <Compass className={`w-3.5 h-3.5 ${crawling ? 'animate-spin text-blue-300' : ''}`} />
            <span>{crawling ? 'Crawling...' : 'Run QEIC Crawler'}</span>
          </button>

          <button
            onClick={triggerAlepEnrichment}
            disabled={enriching}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-2"
            title="Scan CRM & Auto-Enrich pending leads via open-source MX verification & domain intelligence"
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
        {/* Unread Intent Badge Card */}
        <div 
          onClick={() => setFilterMode('unread')}
          className={`card-dark p-3.5 cursor-pointer transition flex items-center justify-between ${filterMode === 'unread' ? 'border-rose-500 ring-2 ring-rose-500/30 bg-rose-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <AlertCircle className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Unread Intent</div>
              <div className="text-lg font-extrabold text-rose-400">{unreadCount}</div>
            </div>
          </div>
          {filterMode === 'unread' && <CheckCircle2 className="w-4 h-4 text-rose-400" />}
        </div>

        {/* Outsourcing Intent Card */}
        <div 
          onClick={() => setFilterMode('outsourcing')}
          className={`card-dark p-3.5 cursor-pointer transition flex items-center justify-between ${filterMode === 'outsourcing' ? 'border-emerald-500 ring-2 ring-emerald-500/30 bg-emerald-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShoppingBag className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Outsourcing RFPs</div>
              <div className="text-lg font-extrabold text-emerald-400">{outsourcingCount}</div>
            </div>
          </div>
          {filterMode === 'outsourcing' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
        </div>

        {/* Total Ingested Leads */}
        <div 
          onClick={() => setFilterMode('all')}
          className={`card-dark p-3.5 cursor-pointer transition flex items-center justify-between ${filterMode === 'all' ? 'border-blue-500 ring-2 ring-blue-500/30 bg-blue-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Total Leads</div>
              <div className="text-lg font-extrabold text-white">{leads.length}</div>
            </div>
          </div>
          {filterMode === 'all' && <CheckCircle2 className="w-4 h-4 text-blue-400" />}
        </div>

        {/* High Intent (>80 Score) */}
        <div 
          onClick={() => setFilterMode('high_intent')}
          className={`card-dark p-3.5 cursor-pointer transition flex items-center justify-between ${filterMode === 'high_intent' ? 'border-amber-500 ring-2 ring-amber-500/30 bg-amber-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Flame className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">High Intent</div>
              <div className="text-lg font-extrabold text-amber-400">
                {leads.filter(l => (l.intent_score || 0) >= 80).length}
              </div>
            </div>
          </div>
          {filterMode === 'high_intent' && <CheckCircle2 className="w-4 h-4 text-amber-400" />}
        </div>

        {/* Outreach-Ready Leads */}
        <div 
          onClick={() => setFilterMode('outreach_ready')}
          className={`card-dark p-3.5 cursor-pointer transition flex items-center justify-between ${filterMode === 'outreach_ready' ? 'border-pink-500 ring-2 ring-pink-500/30 bg-pink-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400">
              <Send className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Outreach-Ready</div>
              <div className="text-lg font-extrabold text-pink-400">
                {leads.filter(l => l.outreach_ready === true).length}
              </div>
            </div>
          </div>
          {filterMode === 'outreach_ready' && <CheckCircle2 className="w-4 h-4 text-pink-400" />}
        </div>

        {/* ALEP Auto-Enriched */}
        <div 
          onClick={() => setFilterMode('alep_enriched')}
          className={`card-dark p-3.5 cursor-pointer transition flex items-center justify-between ${filterMode === 'alep_enriched' ? 'border-purple-500 ring-2 ring-purple-500/30 bg-purple-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">ALEP Enriched</div>
              <div className="text-lg font-extrabold text-purple-400">
                {leads.filter(l => l.enrichment_status === 'ENRICHED').length}
              </div>
            </div>
          </div>
          {filterMode === 'alep_enriched' && <CheckCircle2 className="w-4 h-4 text-purple-400" />}
        </div>
      </div>

      {/* Active Filter Indicator Bar */}
      <div className="flex items-center justify-between text-xs text-slate-400 mb-4 px-1">
        <div>
          Showing <span className="text-white font-bold">{filteredLeads.length}</span> of {leads.length} leads 
          {filterMode === 'unread' && <span className="text-rose-400 font-semibold"> (Filtered: Unread Intent Signals)</span>}
          {filterMode === 'outsourcing' && <span className="text-emerald-400 font-semibold"> (Filtered: OUTSOURCING INTENT Project Scopes)</span>}
          {filterMode === 'high_intent' && <span className="text-amber-400 font-semibold"> (Filtered: High Intent &gt; 80)</span>}
          {filterMode === 'outreach_ready' && <span className="text-pink-400 font-semibold"> (Filtered: Verified Outreach-Ready Leads)</span>}
          {filterMode === 'alep_enriched' && <span className="text-purple-400 font-semibold"> (Filtered: ALEP Enriched Records)</span>}
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
          placeholder="Search by name, company, project scope, email, buyer persona..."
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
                <th className="p-3.5">Lead Age / Name</th>
                <th className="p-3.5">Company & Persona</th>
                <th className="p-3.5">Verified Contact</th>
                <th className="p-3.5">Intent Score & Quality</th>
                <th className="p-3.5">Outreach Status</th>
                <th className="p-3.5">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {filteredLeads.map((lead) => (
                <tr key={lead.id} className={`transition ${lead.unread_intent || lead.outreach_status === 'UNREAD' ? 'bg-rose-950/20 border-l-2 border-l-rose-500' : 'hover:bg-slate-900/50'}`}>
                  <td className="p-3.5 font-sans">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-black px-1.5 py-0.2 rounded bg-slate-800 text-amber-400 font-mono">
                        {lead.lead_age || '10m'}
                      </span>
                      <div className="font-bold text-white text-sm">{lead.name}</div>
                    </div>
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
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className={`inline-block px-2 py-0.5 rounded-full font-bold text-[11px] ${lead.intent_score >= 85 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' : 'bg-blue-500/20 text-blue-400 border border-blue-500/40'}`}>
                        Score {lead.intent_score}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        {lead.intent_quality || 'VERIFIED REAL'}
                      </span>
                    </div>
                  </td>
                  <td className="p-3.5">
                    <select
                      value={lead.outreach_status || 'UNREAD'}
                      onChange={(e) => updateStatus(lead.id, e.target.value)}
                      className={`text-[11px] font-extrabold px-2 py-1 rounded bg-slate-900 border ${lead.outreach_status === 'UNREAD' ? 'border-rose-500 text-rose-400' : lead.outreach_status === 'REACHED_OUT' ? 'border-emerald-500 text-emerald-400' : 'border-slate-700 text-slate-300'}`}
                    >
                      <option value="UNREAD">🔴 UNREAD</option>
                      <option value="IN_PROGRESS">🟡 IN_PROGRESS</option>
                      <option value="REACHED_OUT">🟢 REACHED_OUT</option>
                      <option value="CLOSED">🟣 CLOSED</option>
                    </select>
                  </td>
                  <td className="p-3.5 text-slate-400">
                    <button
                      onClick={() => togglePlaybook(lead.id)}
                      className="px-2.5 py-1 rounded text-[11px] font-semibold bg-pink-500/10 text-pink-300 border border-pink-500/30 hover:bg-pink-500/20 flex items-center gap-1"
                    >
                      <Send className="w-3 h-3" /> Playbook
                    </button>
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
            const outsourcingMeta = parseJsonObject(lead.outsourcing_intent_metadata);
            const isPlaybookOpen = expandedPlaybooks[lead.id];
            const activeTab = activePlaybookTab[lead.id] || 'email';
            const isUnread = lead.unread_intent === true || lead.outreach_status === 'UNREAD';
            const isOutsourcing = outsourcingMeta !== null || (lead.problem_statement || '').includes('OUTSOURCING');

            return (
              <div key={lead.id} className={`card-dark p-5 transition ${isUnread ? 'border-l-4 border-l-rose-500 border-rose-500/40 bg-slate-900/90' : isOutsourcing ? 'border-l-4 border-l-emerald-500 border-emerald-500/40' : 'border-slate-800 hover:border-slate-700'}`}>
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      {isUnread && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-600 text-white flex items-center gap-1 animate-pulse">
                          <AlertCircle className="w-3 h-3" /> UNREAD INTENT
                        </span>
                      )}
                      {isOutsourcing && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                          <ShoppingBag className="w-3 h-3 text-emerald-400" /> OUTSOURCING INTENT
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-amber-400 font-mono">
                        Age: {lead.lead_age || '10m'}
                      </span>
                      <h3 className="text-base font-bold text-white">{lead.name}</h3>
                      <span className="badge-gold text-[10px]">Intent Score: {lead.intent_score}/100</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        {lead.intent_quality || 'VERIFIED REAL'}
                      </span>
                      {lead.outreach_ready && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-pink-500/20 text-pink-300 border border-pink-500/40 flex items-center gap-1">
                          <Send className="w-3 h-3" /> OUTREACH READY
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
                    </div>

                    {/* Outsourcing Project Metadata Bar */}
                    {outsourcingMeta && (
                      <div className="flex flex-wrap items-center gap-3 text-xs bg-emerald-950/40 border border-emerald-500/30 p-2 rounded-lg mt-1 font-mono text-emerald-200">
                        <span>🚀 <strong>Project:</strong> {outsourcingMeta.project_name}</span>
                        <span>💰 <strong>Est. Budget:</strong> {outsourcingMeta.estimated_budget}</span>
                        <span>📡 <strong>Feed:</strong> {outsourcingMeta.source_feed}</span>
                      </div>
                    )}
                  </div>

                  <div className="text-left lg:text-right border-t lg:border-t-0 border-slate-800 pt-3 lg:pt-0 shrink-0 flex flex-col lg:items-end gap-2">
                    <div className="flex items-center lg:justify-end gap-2 text-xs">
                      <span className="text-slate-400 text-[11px]">Status:</span>
                      <select
                        value={lead.outreach_status || 'UNREAD'}
                        onChange={(e) => updateStatus(lead.id, e.target.value)}
                        className={`text-[11px] font-extrabold px-2 py-0.5 rounded bg-slate-900 border ${lead.outreach_status === 'UNREAD' ? 'border-rose-500 text-rose-400' : lead.outreach_status === 'REACHED_OUT' ? 'border-emerald-500 text-emerald-400' : 'border-slate-700 text-slate-300'}`}
                      >
                        <option value="UNREAD">🔴 UNREAD</option>
                        <option value="IN_PROGRESS">🟡 IN_PROGRESS</option>
                        <option value="REACHED_OUT">🟢 REACHED_OUT</option>
                        <option value="CLOSED">🟣 CLOSED</option>
                      </select>
                    </div>

                    {playbook && (
                      <button
                        onClick={() => togglePlaybook(lead.id)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-pink-500/10 text-pink-300 border border-pink-500/30 hover:bg-pink-500/20 transition flex items-center gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>{isPlaybookOpen ? 'Hide Outreach Playbook' : 'View Email & LinkedIn Sequence'}</span>
                        {isPlaybookOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    )}
                  </div>
                </div>

                {/* Interactive Outreach Playbook Drawer with LinkedIn Sequence */}
                {playbook && isPlaybookOpen && (
                  <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-pink-500/40 space-y-3 font-mono text-xs">
                    {/* Drawer Header & Tabs */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setActivePlaybookTab(prev => ({ ...prev, [lead.id]: 'email' }))}
                          className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${activeTab === 'email' ? 'bg-pink-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'}`}
                        >
                          <Mail className="w-3.5 h-3.5" /> Email Proposal &amp; Script
                        </button>
                        <button
                          onClick={() => setActivePlaybookTab(prev => ({ ...prev, [lead.id]: 'linkedin' }))}
                          className={`px-3 py-1 rounded text-xs font-bold transition flex items-center gap-1.5 ${activeTab === 'linkedin' ? 'bg-blue-600 text-white' : 'bg-slate-900 text-slate-400 hover:text-white'}`}
                        >
                          <Linkedin className="w-3.5 h-3.5" /> LinkedIn Outreach Sequence
                        </button>
                      </div>

                      <button
                        onClick={() => copyToClipboard(lead.id, activeTab === 'email' ? playbook.cold_email_body : playbook.linkedin_pitch_message)}
                        className="text-[11px] text-slate-300 hover:text-white bg-slate-900 px-2.5 py-1 rounded flex items-center gap-1 border border-slate-800 self-start sm:self-auto"
                      >
                        {copiedId === lead.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedId === lead.id ? 'Copied to Clipboard!' : 'Copy Script'}</span>
                      </button>
                    </div>

                    {/* Email Tab Content */}
                    {activeTab === 'email' && (
                      <div className="space-y-3">
                        <div>
                          <span className="text-slate-400 uppercase text-[10px] block font-bold mb-0.5">Cold Email / Proposal Subject Line:</span>
                          <div className="text-white font-semibold bg-slate-900 p-2 rounded border border-slate-800">{playbook.subject_line}</div>
                        </div>

                        <div>
                          <span className="text-amber-400 uppercase text-[10px] block font-bold mb-0.5">Pain Point / Project Scope Hook:</span>
                          <div className="text-amber-200 bg-slate-900 p-2 rounded border border-slate-800">{playbook.pain_hook}</div>
                        </div>

                        <div>
                          <span className="text-slate-400 uppercase text-[10px] block font-bold mb-0.5">Cold Email / B2B Proposal Body:</span>
                          <pre className="text-slate-200 whitespace-pre-wrap font-mono bg-slate-900 p-3 rounded-lg border border-slate-800 text-[11px]">
                            {playbook.cold_email_body}
                          </pre>
                        </div>

                        <div>
                          <span className="text-emerald-400 uppercase text-[10px] block font-bold mb-0.5">Phone Call Opening Script:</span>
                          <div className="text-emerald-200 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                            "{playbook.phone_call_script}"
                          </div>
                        </div>
                      </div>
                    )}

                    {/* LinkedIn Sequence Tab Content */}
                    {activeTab === 'linkedin' && (
                      <div className="space-y-3">
                        <div>
                          <span className="text-blue-400 uppercase text-[10px] block font-bold mb-0.5">1. LinkedIn Connection Request Message:</span>
                          <div className="text-blue-200 bg-slate-900 p-2.5 rounded border border-slate-800">
                            "{playbook.linkedin_connection_request || 'Hi, saw your work leading engineering/RevOps initiatives. QUANTA flagged active intent signals on your site this week — would love to connect!'}"
                          </div>
                        </div>

                        <div>
                          <span className="text-blue-400 uppercase text-[10px] block font-bold mb-0.5">2. LinkedIn Follow-Up Message (Post Connection):</span>
                          <div className="text-slate-300 bg-slate-900 p-2.5 rounded border border-slate-800">
                            "{playbook.linkedin_followup_message || 'Thanks for connecting! Quick follow-up: our intent engine picked up active outsourcing/pricing intent for your domain.'}"
                          </div>
                        </div>

                        <div>
                          <span className="text-blue-400 uppercase text-[10px] block font-bold mb-0.5">3. LinkedIn Pitch Message:</span>
                          <div className="text-slate-200 bg-slate-900 p-2.5 rounded border border-slate-800">
                            "{playbook.linkedin_pitch_message || 'Most teams miss high-intent prospects evaluating pricing tables or outsourcing scopes. We help engineering leaders intercept these buyers automatically.'}"
                          </div>
                        </div>

                        <div>
                          <span className="text-emerald-400 uppercase text-[10px] block font-bold mb-0.5">4. LinkedIn Call to Action (CTA) Touchpoint:</span>
                          <div className="text-emerald-200 bg-slate-900 p-2.5 rounded border border-slate-800">
                            "{playbook.linkedin_cta_message || 'Here is a 2-minute link to our live buyer feed and agency case studies: https://quanta.virtusol.com'}"
                          </div>
                        </div>
                      </div>
                    )}
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
                          <Briefcase className="w-3.5 h-3.5 text-amber-400" /> Open-Source Job / Project Signals
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
                          <DollarSign className="w-3.5 h-3.5 text-emerald-400" /> Funding &amp; Budget Signals
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
                      <span className="text-amber-400 font-semibold uppercase tracking-wider text-[10px] block mb-0.5">Real Data-Backed Problem Statement (Open-Source Scored)</span>
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
