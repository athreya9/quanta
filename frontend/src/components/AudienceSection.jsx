import React from 'react';
import { Target, Building2, BarChart3, CheckCircle2 } from 'lucide-react';

export default function AudienceSection() {
  const audiences = [
    {
      title: "Growth & Outbound Agencies",
      icon: Target,
      tag: "High Velocity",
      benefit: "Beat competing agencies to brand-new opportunities before accounts publish RFPs or issue vendor tenders.",
      points: [
        "First-mover advantage on buyer pain signals",
        "Outbound campaigns triggered within seconds",
        "Client white-labeling & instant Slack alerts"
      ]
    },
    {
      title: "B2B SaaS Sales Teams",
      icon: Building2,
      tag: "Pipeline Multiplier",
      benefit: "Intercept active prospects while they are actively evaluating competitor pricing pages and technographic shifts.",
      points: [
        "Competitor evaluation page monitoring",
        "Decision-maker LinkedIn & email enrichment",
        "Chrome Extension live rep assistance"
      ]
    },
    {
      title: "RevOps & Demand Generation",
      icon: BarChart3,
      tag: "Operational Speed",
      benefit: "Eliminate dead leads and route hot, scored accounts directly to account executives without manual triage.",
      points: [
        "Real-time intent scoring algorithms",
        "Native CRM integration & deduplication",
        "Bi-directional attribution analytics"
      ]
    }
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-slate-900/40 rounded-3xl my-12 border border-slate-800/80">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <span className="badge-gold mb-3">Target Ecosystem</span>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          Engineered for Teams Where Every Minute Counts
        </h2>
        <p className="text-slate-300 text-base sm:text-lg">
          If your deal velocity depends on hitting buyers at the exact moment of intent, QUANTA is your unfair revenue advantage.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {audiences.map((aud, i) => {
          const Icon = aud.icon;
          return (
            <div key={i} className="card-dark p-6 sm:p-8 flex flex-col justify-between border-slate-800">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="badge-blue">{aud.tag}</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{aud.title}</h3>
                <p className="text-sm text-slate-300 mb-6 leading-relaxed">
                  {aud.benefit}
                </p>
                <ul className="space-y-3 mb-6">
                  {aud.points.map((pt, j) => (
                    <li key={j} className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
