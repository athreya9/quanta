import React from 'react';
import { Download, ShieldCheck } from 'lucide-react';

export default function LogoDownloader() {
  return (
    <div className="card-dark p-6 max-w-xl mx-auto my-12 border-slate-800 text-center">
      <div className="flex items-center justify-center gap-2 mb-2">
        <ShieldCheck className="w-5 h-5 text-blue-400" />
        <h4 className="text-base font-bold text-white">Download Official Branding Asset</h4>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Download the vector infinity QUANTA logo emblem in crisp SVG format. Guaranteed 100% clean vector with no watermark.
      </p>

      <div className="flex items-center justify-center gap-4">
        <a 
          href="/quanta_logo.svg" 
          download="QUANTA_Logo_Clean.svg"
          className="btn-primary text-xs py-2 px-4 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          <span>Download Logo (SVG)</span>
        </a>
      </div>
    </div>
  );
}
