import React, { useState } from 'react';
import { Code, Copy, Check, FileCode, ShieldCheck } from 'lucide-react';

export const SDKAndManifest: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'python' | 'manifest'>('python');
  const [copied, setCopied] = useState(false);

  const pythonCode = `from emerge import Agent, CanvasKit

agent = Agent(name="web-scraper", did="did:orcha:agent:web-scraper")

@agent.on_goal("summarize_url")
def handle(payload):
    return CanvasKit.Dashboard([
        CanvasKit.Alert(title="Summary", body="Extracted key article contents."),
    ])`;

  const yamlSpec = `schema_version: "1.1"
kind: agent

identity:
  id: "did:orcha:agent:web-scraper"
  name: "Web Scraper Agent"
  version: "1.0.0"
  description: "Extracts and summarizes article contents from URLs."

protocol:
  type: a2a
  version: "1.0"
  transport:
    type: sse
    endpoint: "http://localhost:3007/.well-known/agent.json"

health_endpoint: "http://localhost:3007/health"

security:
  transport_layer:
    type: none
  auth_strategies:
    - id: standard_token
      type: http_bearer
      config: {}
      capability_ids:
        - "web.read"
        - "canvaskit.render"`;

  const currentCode = activeTab === 'python' ? pythonCode : yamlSpec;

  const handleCopy = () => {
    navigator.clipboard.writeText(currentCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="sdk" className="py-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
            Developer SDK
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
            Emerge SDK and agent manifest
          </h2>
          <p className="text-[var(--muted)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            Write specialized agents in standard Python. Orcha handles routing, discovery, identity, and CanvasKit dashboard rendering automatically.
          </p>
        </div>

        {/* Code Window Container */}
        <div className="border border-[var(--line)] rounded-xl overflow-hidden bg-[#080C14] shadow-sm">
          
          {/* Window Header with Tabs */}
          <div className="px-4 py-2.5 border-b border-slate-800 bg-[#0c0f17] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('python')}
                className={`px-3 py-1 rounded-md text-xs font-mono flex items-center gap-1.5 transition-colors ${
                  activeTab === 'python'
                    ? 'bg-[#6366f1]/10 text-white border border-[#6366f1] font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Code className="w-3.5 h-3.5 text-[#6366f1]" /> server.py
              </button>
              <button
                onClick={() => setActiveTab('manifest')}
                className={`px-3 py-1 rounded-md text-xs font-mono flex items-center gap-1.5 transition-colors ${
                  activeTab === 'manifest'
                    ? 'bg-[#6366f1]/10 text-white border border-[#6366f1] font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <FileCode className="w-3.5 h-3.5 text-[#6366f1]" /> emerge.yaml
              </button>
            </div>

            <button
              onClick={handleCopy}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-mono text-[11px] flex items-center gap-1.5 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#6366f1]" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          {/* Code View */}
          <pre className="p-5 font-mono text-xs text-slate-200 leading-relaxed bg-[#080C14] overflow-x-auto">
            <code>{currentCode}</code>
          </pre>

          {/* Footer note */}
          <div className="px-4 py-2 border-t border-slate-800 bg-[#0c0f17] font-mono text-[11px] text-slate-400 flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-[#6366f1]" />
            Schema-enforced DIDs (<code className="text-white font-semibold">identity.id</code>) and capability grants (<code className="text-white font-semibold">auth_strategies[].capability_ids</code>)
          </div>

        </div>

      </div>
    </section>
  );
};
