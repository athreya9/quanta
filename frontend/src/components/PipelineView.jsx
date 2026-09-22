import React, { useState, useEffect } from 'react';
import {
  Building, Target, RefreshCw, Search, Filter, ChevronDown, ChevronUp, Copy, Check,
  ExternalLink, Plus, X, Zap, ShieldCheck, AlertCircle, Trash2, Edit3, Users, Globe,
  Layers, Send, Database, Sparkles
} from 'lucide-react';

const FIT_STYLES = {
  HIGH: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  MEDIUM: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  LOW: 'bg-slate-600/30 text-slate-400 border-slate-600/50',
  UNSCORED: 'bg-slate-800 text-slate-500 border-slate-700',
  EXCLUDED: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
};

const OPERATORS = ['contains_any', 'contains_all', 'in', 'equals', 'between', 'gte', 'lte', 'is_true', 'is_false'];

export default function PipelineView() {
  const [icps, setIcps] = useState([]);
  const [selectedIcpId, setSelectedIcpId] = useState(null);
  const [fitFilter, setFitFilter] = useState('MEDIUM');
  const [companies, setCompanies] = useState([]);
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [busyAction, setBusyAction] = useState(null);
  const [error, setError] = useState(null);

  const [showSeed, setShowSeed] = useState(false);
  const [seedText, setSeedText] = useState('');
  const [seeding, setSeeding] = useState(false);

  const [showIcpForm, setShowIcpForm] = useState(false);
  const [editingIcp, setEditingIcp] = useState(null);
  const [availableFields, setAvailableFields] = useState([]);

  const selectedIcp = icps.find(i => i.id === selectedIcpId);

  const fetchIcps = async () => {
    try {
      const res = await fetch('/api/v1/icp');
      if (res.ok) {
        const data = await res.json();
        setIcps(data);
        if (!selectedIcpId && data.length > 0) setSelectedIcpId(data[0].id);
      }
    } catch (e) { console.error(e); }
  };

  const fetchFields = async () => {
    try {
      const res = await fetch('/api/v1/icp/fields');
      if (res.ok) setAvailableFields((await res.json()).available_fields || []);
    } catch (e) { console.error(e); }
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (selectedIcpId) {
        const res = await fetch(`/api/v1/icp/${selectedIcpId}/qualified-leads?min_fit=${fitFilter}&limit=100`);
        if (res.ok) { setDigest(await res.json()); setCompanies(null); }
        else throw new Error('Failed to load qualified leads');
      } else {
        const res = await fetch('/api/v1/companies?limit=200');
        if (res.ok) { setCompanies(await res.json()); setDigest(null); }
        else throw new Error('Failed to load companies');
      }
    } catch (e) {
      setError(e.message);
      setCompanies([]);
      setDigest(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchIcps(); fetchFields(); }, []);
  useEffect(() => { fetchData(); }, [selectedIcpId, fitFilter]);

  const runAction = async (label, url, method = 'POST') => {
    setBusyAction(label);
    try {
      const res = await fetch(url, { method });
      const data = await res.json().catch(() => ({}));
      alert(`${label}: ${JSON.stringify(data, null, 2).slice(0, 500)}`);
      await fetchData();
    } catch (e) {
      alert(`${label} failed: ${e.message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const submitSeed = async () => {
    setSeeding(true);
    try {
      const domains = seedText.split('\n').map(l => l.trim()).filter(Boolean);
      const companiesPayload = domains.map(line => {
        const [domain, name] = line.split('|').map(s => s && s.trim());
        return { domain, company_name: name || undefined };
      });
      const res = await fetch('/api/v1/companies/seed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies: companiesPayload, icp_profile_id: selectedIcpId || undefined })
      });
      const data = await res.json();
      alert(`Seeded: ${data.newly_added} new, ${data.already_existed} already existed, ${data.industry_inferred_from_homepage} industries inferred`);
      setShowSeed(false);
      setSeedText('');
      await fetchData();
    } catch (e) {
      alert('Seed failed: ' + e.message);
    } finally {
      setSeeding(false);
    }
  };

  const copyToClipboard = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const rows = digest ? digest.leads : (companies || []);
  const filteredRows = rows.filter(r => {
    const name = (r.company_name || r.domain || '').toLowerCase();
    return name.includes(searchTerm.toLowerCase()) || (r.domain || '').includes(searchTerm.toLowerCase());
  });

  return (
    <div className="pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <Layers className="w-6 h-6 text-blue-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Pipeline</h1>
            <span className="badge-gold">Single Source of Truth</span>
          </div>
          <p className="text-sm text-slate-300">
            Every company here traces to a real signal - a real job post, a real funding filing, a real registry record. Nothing is generated to fill space.
          </p>
        </div>
      </div>

      {/* ICP Selector Row */}
      <div className="card-dark p-4 mb-6 border-slate-800">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Project ICP</span>
          </div>
          <select
            value={selectedIcpId || ''}
            onChange={e => setSelectedIcpId(e.target.value ? Number(e.target.value) : null)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All companies (no ICP filter)</option>
            {icps.map(icp => (
              <option key={icp.id} value={icp.id}>{icp.name}{icp.is_active ? '' : ' (inactive)'}</option>
            ))}
          </select>

          {selectedIcpId && (
            <div className="flex items-center gap-1.5">
              {['HIGH', 'MEDIUM', 'LOW'].map(f => (
                <button
                  key={f}
                  onClick={() => setFitFilter(f)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition ${fitFilter === f ? FIT_STYLES[f] : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-white'}`}
                >
                  {f}+
                </button>
              ))}
            </div>
          )}

          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search companies..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center gap-2 ml-auto flex-wrap">
            <button onClick={() => setShowSeed(true)} className="btn-primary text-xs py-2 px-3 flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5" /> Seed Companies
            </button>
            <button
              onClick={() => { setEditingIcp(null); setShowIcpForm(true); }}
              className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
            >
              <Target className="w-3.5 h-3.5" /> New ICP
            </button>
            {selectedIcp && (
              <button
                onClick={() => { setEditingIcp(selectedIcp); setShowIcpForm(true); }}
                className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
              >
                <Edit3 className="w-3.5 h-3.5" /> Edit ICP
              </button>
            )}
          </div>
        </div>

        {selectedIcp && selectedIcp.description && (
          <p className="text-xs text-slate-400 mt-3 pl-1">{selectedIcp.description}</p>
        )}
      </div>

      {/* Action bar - real data sources, one click */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <span className="text-[11px] text-slate-500 uppercase tracking-wider font-bold mr-1">Run discovery:</span>
        <button disabled={busyAction} onClick={() => runAction('QEIC crawler (Greenhouse/Lever hiring)', '/api/v1/crawler/run')} className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/50 transition disabled:opacity-50">
          {busyAction === 'QEIC crawler (Greenhouse/Lever hiring)' ? '...' : 'Hiring signals'}
        </button>
        <button disabled={busyAction} onClick={() => runAction('SEC EDGAR Form D', '/api/v1/discovery/sec-edgar?days_back=7')} className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/50 transition disabled:opacity-50">
          {busyAction === 'SEC EDGAR Form D' ? '...' : 'SEC EDGAR (US funding)'}
        </button>
        <button disabled={busyAction} onClick={() => runAction('UK Companies House', '/api/v1/discovery/uk-companies-house')} className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/50 transition disabled:opacity-50">
          {busyAction === 'UK Companies House' ? '...' : 'UK Companies House'}
        </button>
        <button disabled={busyAction} onClick={() => runAction('Outsourcing RSS', '/api/v1/crawler/outsourcing')} className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/50 transition disabled:opacity-50">
          {busyAction === 'Outsourcing RSS' ? '...' : 'Reddit/Upwork RSS'}
        </button>
        <span className="w-px h-5 bg-slate-800 mx-1" />
        <button disabled={busyAction} onClick={() => runAction('Backfill', '/api/v1/companies/backfill')} className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition disabled:opacity-50">
          Backfill
        </button>
        <button disabled={busyAction} onClick={() => runAction('Rescore all', '/api/v1/companies/rescore')} className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition disabled:opacity-50 flex items-center gap-1.5">
          <RefreshCw className="w-3 h-3" /> Rescore all
        </button>
      </div>

      {/* Summary strip */}
      {digest && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
          <div className="card-dark p-3 border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Qualified ({fitFilter}+)</div>
            <div className="text-xl font-extrabold text-white">{digest.total_qualified}</div>
          </div>
          <div className="card-dark p-3 border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Ready to Send</div>
            <div className="text-xl font-extrabold text-emerald-400">{digest.ready_to_send_count}</div>
          </div>
          <div className="card-dark p-3 border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">No Real Signal Yet</div>
            <div className="text-xl font-extrabold text-slate-500">{digest.total_qualified - digest.ready_to_send_count}</div>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="card-dark p-12 text-center text-slate-400">Loading real data...</div>
      ) : error ? (
        <div className="card-dark p-12 text-center text-rose-400">{error}</div>
      ) : filteredRows.length === 0 ? (
        <div className="card-dark p-12 text-center text-slate-400">
          <p className="mb-2">No companies match yet.</p>
          <p className="text-xs text-slate-500">This is honest, not broken - seed real companies or run a discovery pass above.</p>
        </div>
      ) : (
        <div className="card-dark border-slate-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-400">
                <th className="px-4 py-3 font-semibold">Company</th>
                <th className="px-4 py-3 font-semibold">Industry</th>
                <th className="px-4 py-3 font-semibold">Country</th>
                {digest && <th className="px-4 py-3 font-semibold">Fit</th>}
                {digest && <th className="px-4 py-3 font-semibold">Draft</th>}
                {!digest && <th className="px-4 py-3 font-semibold">Discovered Via</th>}
              </tr>
            </thead>
            <tbody>
              {filteredRows.map(row => (
                <tr
                  key={row.company_id || row.id}
                  onClick={() => setSelected(row)}
                  className="border-b border-slate-800/60 hover:bg-slate-900/60 cursor-pointer transition"
                >
                  <td className="px-4 py-3">
                    <div className="font-semibold text-white">{row.company_name || row.domain}</div>
                    <div className="text-xs text-slate-500 font-mono">{row.domain}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{row.industry || <span className="text-slate-600">unknown</span>}</td>
                  <td className="px-4 py-3 text-slate-300">{row.country || <span className="text-slate-600">unknown</span>}</td>
                  {digest && (
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black border ${FIT_STYLES[row.fit] || FIT_STYLES.UNSCORED}`}>
                        {row.fit} {row.score != null && `${row.score}%`}
                      </span>
                    </td>
                  )}
                  {digest && (
                    <td className="px-4 py-3">
                      {row.drafted ? (
                        <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> Ready</span>
                      ) : (
                        <span className="text-slate-500 text-xs flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" /> No signal</span>
                      )}
                    </td>
                  )}
                  {!digest && <td className="px-4 py-3 text-slate-400 text-xs font-mono">{row.first_discovered_source}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Drawer */}
      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={() => setSelected(null)}>
          <div className="w-full max-w-lg h-full bg-slate-950 border-l border-slate-800 overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">{selected.company_name || selected.domain}</h2>
              <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="text-xs text-slate-500 font-mono mb-4">{selected.domain}</div>

            {selected.fit && (
              <div className="mb-5">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2">Fit Reasoning ({selected.fit}, {selected.score}%)</div>
                <ul className="space-y-1.5">
                  {(selected.fit_reasons || []).map((r, i) => (
                    <li key={i} className="text-xs text-slate-300 bg-slate-900 rounded-lg px-3 py-2 border border-slate-800">{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {selected.cited_signals && selected.cited_signals.length > 0 && (
              <div className="mb-5">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2">Cited Real Signals</div>
                <div className="space-y-2">
                  {selected.cited_signals.map((s, i) => (
                    <div key={i} className="bg-slate-900 rounded-lg p-3 border border-slate-800 text-xs">
                      <div className="text-slate-300 mb-1">{s.fact}</div>
                      <div className="flex items-center justify-between text-slate-500">
                        <span>{s.detected_at ? s.detected_at.slice(0, 10) : ''} · {s.source}</span>
                        {s.source_url && (
                          <a href={s.source_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300 flex items-center gap-1">
                            Source <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selected.drafted && (
              <div className="mb-5">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Outreach Draft</div>
                  <button
                    onClick={() => copyToClipboard(selected.company_id, `${selected.subject_line}\n\n${selected.email_body}`)}
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    {copiedId === selected.company_id ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedId === selected.company_id ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                  <div className="text-sm font-semibold text-white mb-2">{selected.subject_line}</div>
                  <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans">{selected.email_body}</pre>
                </div>
              </div>
            )}

            {selected.draft_skipped_reason && (
              <div className="bg-amber-950/30 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300">
                {selected.draft_skipped_reason}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Seed Modal */}
      {showSeed && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowSeed(false)}>
          <div className="w-full max-w-lg bg-slate-950 border border-slate-800 rounded-2xl p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-2">Seed Real Companies</h3>
            <p className="text-xs text-slate-400 mb-4">One per line: <code className="text-slate-300">domain.com</code> or <code className="text-slate-300">domain.com | Company Name</code>. Every crawler starts watching these for real signals immediately.</p>
            <textarea
              value={seedText}
              onChange={e => setSeedText(e.target.value)}
              rows={8}
              placeholder={"example-industrial.com | Example Industrial GmbH\nanother-domain.com"}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
            />
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowSeed(false)} className="btn-secondary text-xs py-2 px-4">Cancel</button>
              <button onClick={submitSeed} disabled={seeding || !seedText.trim()} className="btn-primary text-xs py-2 px-4">
                {seeding ? 'Seeding...' : 'Seed Companies'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ICP Form Modal */}
      {showIcpForm && (
        <IcpFormModal
          icp={editingIcp}
          availableFields={availableFields}
          onClose={() => setShowIcpForm(false)}
          onSaved={async (savedId) => {
            setShowIcpForm(false);
            await fetchIcps();
            setSelectedIcpId(savedId);
          }}
        />
      )}
    </div>
  );
}

function IcpFormModal({ icp, availableFields, onClose, onSaved }) {
  const [name, setName] = useState(icp?.name || '');
  const [description, setDescription] = useState(icp?.description || '');
  const [outreachPitch, setOutreachPitch] = useState(icp?.outreach_pitch || '');
  const [excludedDomains, setExcludedDomains] = useState((icp?.excluded_domains || []).join(', '));
  const [criteria, setCriteria] = useState(
    icp?.criteria?.length ? icp.criteria.map(c => ({ ...c, valueText: Array.isArray(c.value) ? c.value.join(', ') : (c.value ?? '') })) : [{ field: availableFields[0] || '', operator: 'contains_any', valueText: '', weight: 30 }]
  );
  const [saving, setSaving] = useState(false);

  const addCriterion = () => setCriteria([...criteria, { field: availableFields[0] || '', operator: 'contains_any', valueText: '', weight: 20 }]);
  const removeCriterion = (i) => setCriteria(criteria.filter((_, idx) => idx !== i));
  const updateCriterion = (i, patch) => setCriteria(criteria.map((c, idx) => idx === i ? { ...c, ...patch } : c));

  const submit = async () => {
    setSaving(true);
    try {
      const builtCriteria = criteria.filter(c => c.field).map(c => {
        let value = c.valueText;
        if (['contains_any', 'contains_all', 'in'].includes(c.operator)) {
          value = String(c.valueText).split(',').map(s => s.trim()).filter(Boolean);
        } else if (c.operator === 'between') {
          const parts = String(c.valueText).split(',').map(s => Number(s.trim()));
          value = [parts[0] ?? null, parts[1] ?? null];
        } else if (['gte', 'lte'].includes(c.operator)) {
          value = Number(c.valueText);
        } else if (['is_true', 'is_false'].includes(c.operator)) {
          value = null;
        }
        return { field: c.field, operator: c.operator, value, weight: Number(c.weight) || 10 };
      });

      const payload = {
        name,
        description: description || undefined,
        outreach_pitch: outreachPitch || undefined,
        excluded_domains: excludedDomains.trim() ? excludedDomains.split(',').map(s => s.trim()).filter(Boolean) : undefined,
        criteria: builtCriteria,
        is_active: true,
      };

      const res = icp
        ? await fetch(`/api/v1/icp/${icp.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        : await fetch('/api/v1/icp', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });

      if (res.ok) {
        const data = await res.json();
        onSaved(data.id);
      } else {
        const err = await res.json().catch(() => ({}));
        alert('Failed to save ICP: ' + JSON.stringify(err));
      }
    } catch (e) {
      alert('Failed to save ICP: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 overflow-y-auto" onClick={onClose}>
      <div className="w-full max-w-2xl bg-slate-950 border border-slate-800 rounded-2xl p-6 my-8" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">{icp ? 'Edit ICP' : 'New Project ICP'}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>

        <div className="space-y-3">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Project name (e.g. Connect1to1 - Industrial Buyer ICP)" className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white" />
          <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" rows={2} className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white" />

          <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold pt-2">Criteria</div>
          {criteria.map((c, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-2.5">
              <select value={c.field} onChange={e => updateCriterion(i, { field: e.target.value })} className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white">
                {availableFields.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
              <select value={c.operator} onChange={e => updateCriterion(i, { operator: e.target.value })} className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white">
                {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
              </select>
              {!['is_true', 'is_false'].includes(c.operator) && (
                <input
                  value={c.valueText}
                  onChange={e => updateCriterion(i, { valueText: e.target.value })}
                  placeholder={c.operator === 'between' ? 'min, max' : 'value(s), comma-separated'}
                  className="flex-1 min-w-[120px] bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white"
                />
              )}
              <input
                type="number"
                value={c.weight}
                onChange={e => updateCriterion(i, { weight: e.target.value })}
                title="Weight"
                className="w-16 bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white"
              />
              <button onClick={() => removeCriterion(i)} className="text-rose-400 hover:text-rose-300"><Trash2 className="w-4 h-4" /></button>
            </div>
          ))}
          <button onClick={addCriterion} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"><Plus className="w-3.5 h-3.5" /> Add criterion</button>

          <input value={excludedDomains} onChange={e => setExcludedDomains(e.target.value)} placeholder="Excluded domains, comma-separated (existing customers/competitors)" className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white" />

          <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold pt-2">Outreach Pitch (your real copy - not generated)</div>
          <textarea value={outreachPitch} onChange={e => setOutreachPitch(e.target.value)} placeholder="What are you actually offering? This appears verbatim in every draft for this project." rows={3} className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white" />
        </div>

        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="btn-secondary text-xs py-2 px-4">Cancel</button>
          <button onClick={submit} disabled={saving || !name} className="btn-primary text-xs py-2 px-4">{saving ? 'Saving...' : 'Save ICP'}</button>
        </div>
      </div>
    </div>
  );
}
