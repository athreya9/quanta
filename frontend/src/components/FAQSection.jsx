import React, { useState } from 'react';
import { ChevronDown, HelpCircle, ShieldCheck } from 'lucide-react';

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState(0);

  const faqs = [
    {
      q: "How does QUANTA capture micro-signals faster than traditional enrichment tools?",
      a: "Legacy enrichment tools rely on slow batch scraping and weekly database updates. QUANTA connects directly to domain-level traffic streams, SDK webhooks, and technographic listeners. When a prospect installs a competitor tool, changes their tech stack, or visits a high-intent pricing page, QUANTA processes and scores the event in under 150 milliseconds."
    },
    {
      q: "What constitutes your 'Speed Moat' in revenue operations?",
      a: "In modern outbound sales, reaching a buyer within 5 minutes of active intent increases conversion rates by up to 9x compared to reaching out 2 hours later. QUANTA’s speed moat guarantees sub-second signal delivery straight to your sales reps' screens, allowing your SDRs to strike while the buyer's pain point is actively top-of-mind."
    },
    {
      q: "How does QUANTA integrate with Slack and Chrome?",
      a: "QUANTA features direct webhooks and browser extensions. Our Slack bot pushes instant ping cards into designated channel feeds (#quanta-hot-leads), containing account details, intent scores, and pre-generated outreach copy. Our Chrome extension overlays intent alerts directly onto LinkedIn profiles and target company websites as your reps browse."
    },
    {
      q: "Where does QUANTA source its intent data, and is it compliant?",
      a: "QUANTA aggregates first-party website event streams, global B2B IP telemetry, verified job posting feeds, and public technographic change registries. All data processing strictly adheres to GDPR, CCPA, and SOC2 type II compliance standards. We track business entities and domain-level intent, preserving individual consumer privacy."
    },
    {
      q: "How is QUANTA priced?",
      a: "QUANTA offers tiered SaaS pricing based on active intent volume and user seats. All plans include full access to the QUANTA CRM engine, Slack bot notifications, Chrome extension overlays, and unlimited IP-to-company resolution. Contact our team to request a custom volume quote for your revenue target."
    }
  ];

  return (
    <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
      <div className="text-center max-w-2xl mx-auto mb-14">
        <span className="badge-gold mb-3">Direct Answers</span>
        <h2 className="text-3xl font-extrabold text-white mb-3">
          Frequently Asked Questions
        </h2>
        <p className="text-slate-300 text-sm sm:text-base">
          Everything you need to know about QUANTA’s intent engine, delivery architecture, and revenue impact.
        </p>
      </div>

      <div className="space-y-4">
        {faqs.map((faq, idx) => (
          <div 
            key={idx} 
            className="card-dark border-slate-800/90 overflow-hidden transition"
          >
            <button
              onClick={() => setOpenIndex(openIndex === idx ? -1 : idx)}
              className="w-full p-5 text-left flex items-center justify-between gap-4 font-bold text-base text-white hover:text-blue-400 transition"
            >
              <span>{faq.q}</span>
              <ChevronDown className={`w-5 h-5 text-slate-400 shrink-0 transition-transform ${openIndex === idx ? 'rotate-180 text-blue-400' : ''}`} />
            </button>
            {openIndex === idx && (
              <div className="px-5 pb-5 text-sm text-slate-300 leading-relaxed border-t border-slate-800/60 pt-4">
                {faq.a}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
