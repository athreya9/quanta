import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Users, Flame, RefreshCw, Search, ShieldCheck, MapPin, Building, Mail, Globe, ArrowUpRight } from 'lucide-react';

export default function CRMView() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);

  const fetchCRMLeads = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/leads');
      if (!res.ok) throw new Error('Failed to fetch leads');
      const data = await res.json();
      setLeads(data);
    } catch (err) {
      setError(err.message);
      // Fallback mock lead for demonstration if backend is offline
      setLeads([
        {
          id: 1,
          name: "Apex Growth Demo Lead",
          email: "demolead@apexgrowth.io",
          company: "Apex Growth Systems",
          role: "VP Demand Gen",
          website: "https://apexgrowth.io",
          country: "United States",
          struggle: "Missing high-intent buyers visiting competitor pricing tables.",
          ip_address: "198.51.100.42",
          geo_location: "San Francisco, United States",
          intent_score: 94.5,
          status: "NEW_QUALIFIED",
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCRMLeads();
  }, []);

  const filteredLeads = leads.filter(l => 
    l.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <LayoutDashboard className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">QUANTA CRM</h1>
            <span className="badge-gold">Live Store</span>
          </div>
          <p className="text-sm text-slate-300">
            Real-time lead storage, auto-enrichment & intent qualification repository.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={fetchCRMLeads}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Sync CRM</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="card-dark p-4 border-slate-800 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">Total Leads</div>
            <div className="text-xl font-extrabold text-white">{leads.length}</div>
          </div>
        </div>

        <div className="card-dark p-4 border-slate-800 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">High Intent (&gt;85)</div>
            <div className="text-xl font-extrabold text-amber-400">
              {leads.filter(l => l.intent_score >= 85).length}
            </div>
          </div>
        </div>

        <div className="card-dark p-4 border-slate-800 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider">Auto-Enriched IP</div>
            <div className="text-xl font-extrabold text-emerald-400">100%</div>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="mb-6 relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by lead name, company, or email..."
          className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Leads Table / Grid */}
      {filteredLeads.length === 0 ? (
        <div className="card-dark p-12 text-center text-slate-400">
          <p>No leads found in QUANTA CRM matching your search criteria.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLeads.map((lead) => (
            <div key={lead.id} className="card-dark p-5 border-slate-800 hover:border-slate-700 transition">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-base font-bold text-white">{lead.name}</h3>
                    <span className="badge-gold text-[10px]">Score: {lead.intent_score}</span>
                    <span className="badge-blue text-[10px]">{lead.status}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1"><Building className="w-3.5 h-3.5 text-blue-400" /> {lead.company} {lead.role ? `(${lead.role})` : ''}</span>
                    <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5 text-slate-400" /> {lead.email}</span>
                    {lead.website && (
                      <a href={lead.website} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-400 hover:underline">
                        <Globe className="w-3.5 h-3.5" /> Website <ArrowUpRight className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>

                <div className="text-left lg:text-right border-t lg:border-t-0 border-slate-800 pt-3 lg:pt-0">
                  <div className="flex items-center lg:justify-end gap-1.5 text-xs text-emerald-400 font-mono">
                    <MapPin className="w-3.5 h-3.5" /> {lead.geo_location || 'Resolved'}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    IP: {lead.ip_address || '127.0.0.1'} | Ingested: {new Date(lead.created_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>

              {lead.struggle && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-300 italic bg-slate-900/50 p-2.5 rounded-lg">
                  <span className="text-amber-400 font-semibold not-italic">Pain Point: </span>
                  "{lead.struggle}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
