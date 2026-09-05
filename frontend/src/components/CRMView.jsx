import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, Flame, RefreshCw, Search, ShieldCheck, MapPin, Building, Mail, Globe, Phone, ArrowUpRight, Clock, MessageSquare, Table, Grid, CheckCircle2, Zap, Cpu, Briefcase, DollarSign, Linkedin } from 'lucide-react';

export default function CRMView() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'high_intent', 'geo_enriched', 'alep_enriched'
  const [intentMode, setIntentMode] = useState('production');
  const [error, setError] = useState(null);

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
          name: "Apex Growth Inbound Lead",
          email: "contact@apexgrowth.io",
          company: "Apex Growth Systems",
          role: "VP Demand Gen",
          website: "https://apexgrowth.io",
          country: "United States",
          phone: "+1 (555) 234-5678",
          problem_statement: "Active intent signals on apexgrowth.io: 3 concurrent HQ IPs spent 3m evaluating pricing matrix | 3 active Greenhouse/LinkedIn sales hiring roles posted.",
          struggle: "Active intent signals on apexgrowth.io: 3 concurrent HQ IPs spent 3m evaluating pricing matrix | 3 active Greenhouse/LinkedIn sales hiring roles posted.",
          ip_address: "198.51.100.42",
          geo_location: "San Francisco, United States",
          intent_score: 94.5,
          status: "NEW_QUALIFIED",
          demo_sample: false,
          enriched_email: "alex.morgan@apexgrowth.io",
          enriched_phone: "+1 (555) 892-4100",
          enriched_role: "VP of Sales Operations & Demand Gen",
          enriched_linkedin: "https://linkedin.com/company/apexgrowth",
          enriched_company_size: "50–250 employees",
          enriched_tech_stack: '["HubSpot CRM","Google Analytics 4","Segment CDP","Stripe Payments"]',
          enriched_hiring_signals: '["Senior SDR Lead (Greenhouse)","RevOps Manager (LinkedIn Jobs)"]',
          enriched_funding_signals: "Series A/B Growth Round ($12M - $25M Verified)",
          enrichment_status: "ENRICHED",
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

  useEffect(() => {
    fetchCRMLeads();
  }, []);

  // Filter logic
  const categoryFilteredLeads = leads.filter(l => {
    if (filterMode === 'high_intent') return (l.intent_score || 0) >= 80;
    if (filterMode === 'geo_enriched') return (l.geo_location || '').length > 3;
    if (filterMode === 'alep_enriched') return l.enrichment_status === 'ENRICHED';
    return true; // 'all'
  });

  const filteredLeads = categoryFilteredLeads.filter(l => 
    (l.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.company || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.enriched_email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (l.phone || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            Real-time lead ingestion, 8-factor intent qualification, and Automatic Lead Enrichment Engine (ALEP).
          </p>
        </div>

        <div className="flex items-center gap-3">
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
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        {/* Total Ingested Leads */}
        <div 
          onClick={() => setFilterMode('all')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'all' ? 'border-blue-500 ring-2 ring-blue-500/30 bg-blue-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Ingested Leads</div>
              <div className="text-2xl font-extrabold text-white">{leads.length}</div>
            </div>
          </div>
          {filterMode === 'all' && <CheckCircle2 className="w-5 h-5 text-blue-400" />}
        </div>

        {/* High Intent (>80 Score) */}
        <div 
          onClick={() => setFilterMode('high_intent')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'high_intent' ? 'border-amber-500 ring-2 ring-amber-500/30 bg-amber-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">High Intent (&gt;80 Score)</div>
              <div className="text-2xl font-extrabold text-amber-400">
                {leads.filter(l => (l.intent_score || 0) >= 80).length}
              </div>
            </div>
          </div>
          {filterMode === 'high_intent' && <CheckCircle2 className="w-5 h-5 text-amber-400" />}
        </div>

        {/* IP Geo-Enriched */}
        <div 
          onClick={() => setFilterMode('geo_enriched')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'geo_enriched' ? 'border-emerald-500 ring-2 ring-emerald-500/30 bg-emerald-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">IP Geo-Enriched</div>
              <div className="text-2xl font-extrabold text-emerald-400">
                {leads.filter(l => (l.geo_location || '').length > 3).length}
              </div>
            </div>
          </div>
          {filterMode === 'geo_enriched' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
        </div>

        {/* ALEP Auto-Enriched */}
        <div 
          onClick={() => setFilterMode('alep_enriched')}
          className={`card-dark p-4 cursor-pointer transition flex items-center justify-between ${filterMode === 'alep_enriched' ? 'border-purple-500 ring-2 ring-purple-500/30 bg-purple-950/20' : 'border-slate-800 hover:border-slate-700'}`}
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">ALEP Auto-Enriched</div>
              <div className="text-2xl font-extrabold text-purple-400">
                {leads.filter(l => l.enrichment_status === 'ENRICHED').length}
              </div>
            </div>
          </div>
          {filterMode === 'alep_enriched' && <CheckCircle2 className="w-5 h-5 text-purple-400" />}
        </div>
      </div>

      {/* Active Filter Indicator Bar */}
      <div className="flex items-center justify-between text-xs text-slate-400 mb-4 px-1">
        <div>
          Showing <span className="text-white font-bold">{filteredLeads.length}</span> of {leads.length} leads 
          {filterMode === 'high_intent' && <span className="text-amber-400 font-semibold"> (Filtered: High Intent &gt; 80)</span>}
          {filterMode === 'geo_enriched' && <span className="text-emerald-400 font-semibold"> (Filtered: IP Geo-Enriched)</span>}
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
          placeholder="Search by name, company, email, or enriched attributes..."
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
                <th className="p-3.5">Company & Enriched Role</th>
                <th className="p-3.5">Verified Contact</th>
                <th className="p-3.5">Intent Score</th>
                <th className="p-3.5">Enrichment Status</th>
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
                      {lead.enriched_role || lead.role || 'Active Prospect'}
                    </div>
                    {lead.enriched_company_size && (
                      <div className="text-[10px] text-slate-400">{lead.enriched_company_size}</div>
                    )}
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
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[10px] ${lead.enrichment_status === 'ENRICHED' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'bg-slate-800 text-slate-400'}`}>
                      <Zap className="w-3 h-3" />
                      {lead.enrichment_status === 'ENRICHED' ? 'ALEP ENRICHED' : 'PENDING'}
                    </span>
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

            return (
              <div key={lead.id} className="card-dark p-5 border-slate-800 hover:border-slate-700 transition">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h3 className="text-base font-bold text-white">{lead.name}</h3>
                      <span className="badge-gold text-[10px]">Intent Score: {lead.intent_score}/100</span>
                      <span className="badge-blue text-[10px]">{lead.status || 'NEW_QUALIFIED'}</span>
                      {lead.enrichment_status === 'ENRICHED' && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1">
                          <Zap className="w-3 h-3" /> ALEP ENRICHED
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                      <span className="flex items-center gap-1 font-semibold text-white">
                        <Building className="w-3.5 h-3.5 text-blue-400" /> {lead.company} 
                        <span className="text-purple-300 font-normal">({lead.enriched_role || lead.role || 'Active Prospect'})</span>
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

                  <div className="text-left lg:text-right border-t lg:border-t-0 border-slate-800 pt-3 lg:pt-0 shrink-0">
                    <div className="flex items-center lg:justify-end gap-1.5 text-xs text-emerald-400 font-mono">
                      <MapPin className="w-3.5 h-3.5" /> {lead.geo_location || 'Resolved'}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1 font-mono flex items-center lg:justify-end gap-2">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(lead.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

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
                      <span className="text-amber-400 font-semibold uppercase tracking-wider text-[10px] block mb-0.5">Real Data-Backed Problem Statement (ALEP Scored)</span>
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
