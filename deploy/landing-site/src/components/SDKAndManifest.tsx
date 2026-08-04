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
    <section id="sdk" className="py-16 border-b border-black/10 bg-[var(--paper)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-[var(--muted-light)] font-semibold">
            Developer SDK
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--ink)]">
            Orcha SDK and agent manifest
          </h2>
          <p className="text-[var(--muted-light)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            Write specialized agents in standard Python. Orcha handles routing, discovery, identity, and CanvasKit dashboard rendering automatically.
          </p>
        </div>

        {/* Code Window Container */}
        <div className="border border-[var(--line-dark)] rounded-xl overflow-hidden bg-[#050505] shadow-sm">
          
          {/* Window Header with Tabs */}
          <div className="px-4 py-2.5 border-b border-[var(--line-dark)] bg-[#0a0a0a] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('python')}
                className={`px-3 py-1 rounded-md text-xs font-mono flex items-center gap-1.5 transition-colors ${
                  activeTab === 'python'
                    ? 'bg-white/10 text-white border border-white/40 font-semibold'
                    : 'text-[var(--muted-dark)] hover:text-white'
                }`}
              >
                <Code className="w-3.5 h-3.5" /> server.py
              </button>
              <button
                onClick={() => setActiveTab('manifest')}
                className={`px-3 py-1 rounded-md text-xs font-mono flex items-center gap-1.5 transition-colors ${
                  activeTab === 'manifest'
                    ? 'bg-white/10 text-white border border-white/40 font-semibold'
                    : 'text-[var(--muted-dark)] hover:text-white'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" /> emerge.yaml
              </button>
            </div>

            <button
              onClick={handleCopy}
              className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-[var(--muted-dark)] hover:text-white font-mono text-[11px] flex items-center gap-1.5 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-white" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          {/* Code View */}
          <pre className="p-5 font-mono text-xs text-neutral-200 leading-relaxed bg-[#050505] overflow-x-auto">
            <code>{currentCode}</code>
          </pre>

          {/* Footer note */}
          <div className="px-4 py-2 border-t border-[var(--line-dark)] bg-[#0a0a0a] font-mono text-[11px] text-[var(--muted-dark)] flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            Schema-enforced DIDs (<code className="text-white font-semibold">identity.id</code>) and capability grants (<code className="text-white font-semibold">auth_strategies[].capability_ids</code>)
          </div>

        </div>

      </div>
    </section>
  );
};
