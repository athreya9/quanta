import React, { useState } from 'react';
import { Send, CheckCircle2, AlertCircle, ShieldCheck, Sparkles, LayoutDashboard, Phone } from 'lucide-react';

export default function LeadForm({ setActiveTab }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
    website: '',
    country: 'United States',
    phone: '',
    problem_statement: ''
  });

  const [loading, setLoading] = useState(false);
  const [successLead, setSuccessLead] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    setSuccessLead(null);

    try {
      const response = await fetch('/api/v1/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          struggle: formData.problem_statement // Send both for compatibility
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to submit enquiry to QUANTA CRM.');
      }

      const leadResult = await response.json();
      setSuccessLead(leadResult);
      
      // Clear form after success
      setFormData({
        name: '',
        email: '',
        company: '',
        role: '',
        website: '',
        country: 'United States',
        phone: '',
        problem_statement: ''
      });
    } catch (err) {
      setErrorMsg(err.message || 'Error connecting to QUANTA CRM backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="lead-form-section" className="py-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
      <div className="card-dark p-6 sm:p-10 border-blue-500/30 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-[80px] pointer-events-none" />

        <div className="text-center max-w-2xl mx-auto mb-8">
          <span className="badge-blue mb-3">Direct Revenue Access</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-2">
            Get QUANTA Intent Signals for Your Team
          </h2>
          <p className="text-sm sm:text-base text-slate-300">
            Tell us about your target accounts and current lead flow. Every submission is ingested directly into QUANTA’s live CRM engine.
          </p>
        </div>

        {/* Success Alert Toast */}
        {successLead && (
          <div className="mb-8 p-6 rounded-2xl bg-emerald-950/70 border border-emerald-500/50 text-left space-y-4 shadow-xl">
            <div className="flex items-center gap-3 text-emerald-400">
              <CheckCircle2 className="w-6 h-6 shrink-0" />
              <div>
                <h4 className="font-bold text-base text-white">Lead Successfully Ingested into QUANTA CRM</h4>
                <p className="text-xs text-emerald-300">ID #{successLead.id} | Intent Score: {successLead.intent_score}/100 | Status: {successLead.status}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-slate-300 font-mono">
              <div><span className="text-slate-500">Name:</span> {successLead.name}</div>
              <div><span className="text-slate-500">Company:</span> {successLead.company}</div>
              <div><span className="text-slate-500">Phone:</span> {successLead.phone || 'N/A'}</div>
              <div><span className="text-slate-500">IP Geo:</span> {successLead.geo_location}</div>
            </div>

            <div className="pt-2 flex justify-end">
              <button 
                onClick={() => setActiveTab('crm')} 
                className="btn-gold text-xs py-2 px-4 flex items-center gap-2"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>View Lead in QUANTA CRM</span>
              </button>
            </div>
          </div>
        )}

        {/* Error Alert Toast */}
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/70 border border-red-500/50 text-red-300 text-sm flex items-center gap-3 shadow-lg">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-left">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Full Name *
              </label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g. Sarah Jenkins"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Work Email *
              </label>
              <input
                type="email"
                name="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="sarah@company.com"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Company Name *
              </label>
              <input
                type="text"
                name="company"
                required
                value={formData.company}
                onChange={handleChange}
                placeholder="e.g. Apex Revenue Systems"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Your Role
              </label>
              <input
                type="text"
                name="role"
                value={formData.role}
                onChange={handleChange}
                placeholder="e.g. Head of Outbound Sales"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Company Website
              </label>
              <input
                type="url"
                name="website"
                value={formData.website}
                onChange={handleChange}
                placeholder="https://company.com"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Phone Number
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+1 (555) 234-5678"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Country
              </label>
              <select
                name="country"
                value={formData.country}
                onChange={handleChange}
                className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
              >
                <option value="United States">United States</option>
                <option value="United Kingdom">United Kingdom</option>
                <option value="Canada">Canada</option>
                <option value="Australia">Australia</option>
                <option value="India">India</option>
                <option value="Germany">Germany</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Problem Statement / What are you struggling with?
            </label>
            <textarea
              name="problem_statement"
              rows="3"
              value={formData.problem_statement}
              onChange={handleChange}
              placeholder="e.g. Prospects visit our pricing page but exit without converting. We want real-time pings when high-value accounts evaluate us."
              className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
            ></textarea>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5 flex items-center justify-center gap-2 text-base font-semibold"
            >
              {loading ? (
                <span>Ingesting Lead to CRM...</span>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit Lead & Trigger CRM Pipeline</span>
                </>
              )}
            </button>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-400" /> Auto-Enriched IP & Geo-Context
            </span>
            <span>QUANTA Rate Limited API</span>
          </div>
        </form>
      </div>
    </section>
  );
}
