import React, { useState, useMemo, useRef } from 'react';
import {
  Search,
  BookOpen,
  ChevronRight,
  Copy,
  Check,
  Terminal,
  Cpu,
  Layers,
  FileText,
  Layout,
  Rocket,
  ExternalLink,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Info,
  Sparkles,
  Code
} from 'lucide-react';
import { DOCS_CATEGORIES, DocArticle, DocCategory } from '../data/docsData';

interface DocumentationPageProps {
  onNavigateToTab?: (tab: string) => void;
}

export const DocumentationPage: React.FC<DocumentationPageProps> = ({ onNavigateToTab }) => {
  const [selectedArticleId, setSelectedArticleId] = useState<string>('overview');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [copiedCodeIndex, setCopiedCodeIndex] = useState<number | null>(null);

  // Category Icon Map
  const categoryIconMap: Record<string, React.ReactNode> = {
    'getting-started': <Rocket className="w-4 h-4 text-[#6366f1]" />,
    architecture: <Layers className="w-4 h-4 text-[#6366f1]" />,
    bridges: <Cpu className="w-4 h-4 text-[#6366f1]" />,
    spec: <FileText className="w-4 h-4 text-[#6366f1]" />,
    canvaskit: <Layout className="w-4 h-4 text-[#6366f1]" />,
    'sdk-cli': <Terminal className="w-4 h-4 text-[#6366f1]" />
  };

  // Flattened articles list
  const allArticles = useMemo(() => {
    return DOCS_CATEGORIES.flatMap((c) => c.articles);
  }, []);

  // Filtered categories based on search
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) return DOCS_CATEGORIES;

    const query = searchQuery.toLowerCase();
    return DOCS_CATEGORIES.map((cat) => ({
      ...cat,
      articles: cat.articles.filter(
        (art) =>
          art.title.toLowerCase().includes(query) ||
          art.description.toLowerCase().includes(query) ||
          art.content.some((c) => c.value?.toLowerCase().includes(query))
      )
    })).filter((cat) => cat.articles.length > 0);
  }, [searchQuery]);

  // Current Article
  const currentArticle = useMemo(() => {
    return allArticles.find((a) => a.id === selectedArticleId) || allArticles[0];
  }, [allArticles, selectedArticleId]);

  // Article index for Prev/Next
  const currentIndex = useMemo(() => {
    return allArticles.findIndex((a) => a.id === currentArticle.id);
  }, [allArticles, currentArticle]);

  const prevArticle = currentIndex > 0 ? allArticles[currentIndex - 1] : null;
  const nextArticle = currentIndex < allArticles.length - 1 ? allArticles[currentIndex + 1] : null;

  const articleTopRef = useRef<HTMLElement>(null);

  const handleArticleNav = (id: string) => {
    setSelectedArticleId(id);
    articleTopRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedCodeIndex(index);
    setTimeout(() => setCopiedCodeIndex(null), 2000);
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-[var(--bg)] text-[var(--text)] transition-colors">
      
      {/* Docs Header Banner */}
      <div className="border-b border-[var(--line)] bg-[var(--card-bg)]/60 py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
              Developer Docs
            </h1>
            <p className="font-mono text-xs text-[var(--faint)]">
              architecture · spec · sdk
            </p>
          </div>

          {/* Quick Search Input */}
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--faint)]" />
            <input
              type="text"
              placeholder="Search docs, APIs, specs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[var(--bg)] border border-[var(--line)] focus:border-[#6366f1] rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-[var(--text)] placeholder:text-[var(--faint)] outline-none transition-all shadow-sm"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs font-mono text-[var(--faint)] hover:text-[var(--text)]"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Docs Main Layout: Left Sidebar + Main Content */}
      <div className="w-full flex flex-col lg:flex-row">
        
        {/* Left Sidebar Navigation */}
        <aside className="lg:w-72 flex-shrink-0 border-b lg:border-b-0 lg:border-r border-[var(--line)] bg-[var(--bg-raise)] px-4 sm:px-6 py-8 space-y-6">
          <div className="sticky top-20 space-y-6">
            
            {/* Navigation Categories */}
            <nav className="space-y-6 max-h-[calc(100vh-10rem)] overflow-y-auto pr-2 custom-scrollbar">
              {filteredCategories.length === 0 ? (
                <div className="text-xs font-mono text-[var(--faint)] p-3 border border-dashed border-[var(--line)] rounded-lg">
                  No matching doc articles found for "{searchQuery}".
                </div>
              ) : (
                filteredCategories.map((cat) => (
                  <div key={cat.id} className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-[var(--text)] uppercase tracking-wider px-2">
                      {categoryIconMap[cat.id] || <BookOpen className="w-4 h-4 text-[#6366f1]" />}
                      <span>{cat.name}</span>
                    </div>

                    <div className="space-y-0.5 border-l border-[var(--line)] ml-2.5 pl-2.5">
                      {cat.articles.map((art) => {
                        const isActive = art.id === selectedArticleId;
                        return (
                          <button
                            key={art.id}
                            onClick={() => setSelectedArticleId(art.id)}
                            className={`w-full text-left px-2.5 py-1.5 rounded-md font-mono text-xs transition-all flex items-center justify-between group ${
                              isActive
                                ? 'bg-[#6366f1] text-white font-semibold shadow-sm'
                                : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--card-bg)]'
                            }`}
                          >
                            <span className="truncate">{art.title}</span>
                            {isActive && <ChevronRight className="w-3.5 h-3.5 text-white flex-shrink-0" />}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </nav>

            {/* Quick Links Card */}
            <div className="p-4 rounded-xl border border-[var(--line)] bg-[var(--card-bg)] space-y-2.5 font-mono text-xs shadow-sm">
              <div className="font-bold text-[var(--text)] flex items-center justify-between">
                <span>Core Links</span>
                <span className="w-2 h-2 rounded-full bg-[#6366f1]"></span>
              </div>
              <div className="space-y-1.5 text-[var(--muted)]">
                {onNavigateToTab && (
                  <>
                    <button
                      onClick={() => onNavigateToTab('roadmap')}
                      className="block w-full text-left hover:text-[#6366f1] transition-colors flex items-center justify-between py-1"
                    >
                      <span>Interactive Roadmap</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onNavigateToTab('contributing')}
                      className="block w-full text-left hover:text-[#6366f1] transition-colors flex items-center justify-between py-1"
                    >
                      <span>Bridge Contributor Guide</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onNavigateToTab('playground')}
                      className="block w-full text-left hover:text-[#6366f1] transition-colors flex items-center justify-between py-1"
                    >
                      <span>Execution Sandbox</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </>
                )}
                <a
                  href="https://github.com/azank1/orcha"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block hover:text-[#6366f1] transition-colors flex items-center justify-between py-1"
                >
                  <span>GitHub Repository</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

          </div>
        </aside>

        {/* Main Article Render Container */}
        <main ref={articleTopRef} className="flex-1 min-w-0 space-y-8 px-4 sm:px-6 lg:px-8 py-8 scroll-mt-20">
          
          {/* Article Header */}
          <div className="border-b border-[var(--line)] pb-6 space-y-3">
            <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
              <span className="text-[#6366f1] font-semibold">{currentArticle.categoryName}</span>
              <span className="text-[var(--faint)]">/</span>
              <span className="text-[var(--muted)]">{currentArticle.title}</span>
              <span className="ml-auto text-[11px] text-[var(--faint)] bg-[var(--card-bg)] px-2 py-0.5 rounded border border-[var(--line)]">
                {currentArticle.readTime}
              </span>
            </div>

            <h2 className="font-display font-bold text-2xl sm:text-3xl text-[var(--text)] tracking-tight">
              {currentArticle.title}
            </h2>

            <p className="text-sm text-[var(--muted)] leading-relaxed">
              {currentArticle.description}
            </p>
          </div>

          {/* Article Content Blocks */}
          <div className="space-y-6">
            {currentArticle.content.map((block, idx) => {
              if (block.type === 'markdown') {
                return (
                  <div
                    key={idx}
                    className="prose dark:prose-invert max-w-none text-xs sm:text-sm text-[var(--text)] leading-relaxed space-y-3 font-sans"
                  >
                    {block.value?.split('\n\n').map((paragraph, pIdx) => {
                      if (paragraph.startsWith('## ')) {
                        return (
                          <h3 key={pIdx} className="font-display font-bold text-xl text-[var(--text)] mt-6 mb-2 tracking-tight">
                            {paragraph.replace('## ', '')}
                          </h3>
                        );
                      }
                      if (paragraph.startsWith('### ')) {
                        return (
                          <h4 key={pIdx} className="font-display font-bold text-base text-[var(--text)] mt-4 mb-2">
                            {paragraph.replace('### ', '')}
                          </h4>
                        );
                      }
                      if (paragraph.startsWith('1. ') || paragraph.startsWith('- ')) {
                        const items = paragraph.split('\n');
                        return (
                          <ul key={pIdx} className="space-y-1.5 my-2 pl-4 list-disc text-[var(--muted)]">
                            {items.map((item, iIdx) => (
                              <li key={iIdx} className="leading-relaxed">
                                {item.replace(/^[0-9]+\.\s+|^-\s+/, '')}
                              </li>
                            ))}
                          </ul>
                        );
                      }
                      return (
                        <p key={pIdx} className="text-[var(--muted)] leading-relaxed">
                          {paragraph}
                        </p>
                      );
                    })}
                  </div>
                );
              }

              if (block.type === 'code') {
                return (
                  <div key={idx} className="relative group rounded-xl overflow-hidden border border-[var(--line)] bg-[#0A0E17] shadow-sm">
                    {/* Header bar */}
                    <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-[#070A10] font-mono text-[11px] text-slate-400">
                      <div className="flex items-center gap-2">
                        <Code className="w-3.5 h-3.5 text-[#6366f1]" />
                        <span className="uppercase">{block.codeLanguage || 'code'}</span>
                      </div>
                      <button
                        onClick={() => handleCopy(block.value || '', idx)}
                        className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors py-0.5 px-2 rounded hover:bg-slate-800"
                      >
                        {copiedCodeIndex === idx ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-emerald-400 font-semibold">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>

                    {/* Code Body */}
                    <pre className="p-4 font-mono text-xs text-slate-200 overflow-x-auto leading-relaxed custom-scrollbar">
                      <code>{block.value}</code>
                    </pre>
                  </div>
                );
              }

              if (block.type === 'callout') {
                const calloutStyles = {
                  info: 'border-[#6366f1]/40 bg-[#6366f1]/5 text-[#6366f1]',
                  warning: 'border-amber-500/40 bg-amber-500/5 text-amber-500',
                  tip: 'border-emerald-500/40 bg-emerald-500/5 text-emerald-500',
                  success: 'border-indigo-500/40 bg-indigo-500/5 text-indigo-400'
                };

                const calloutIcon = {
                  info: <Info className="w-4 h-4 flex-shrink-0" />,
                  warning: <AlertCircle className="w-4 h-4 flex-shrink-0" />,
                  tip: <Sparkles className="w-4 h-4 flex-shrink-0" />,
                  success: <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                };

                const type = block.calloutType || 'info';

                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border ${calloutStyles[type]} space-y-1.5 shadow-sm`}
                  >
                    <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider">
                      {calloutIcon[type]}
                      <span>{block.calloutTitle || 'Note'}</span>
                    </div>
                    <p className="text-xs sm:text-sm text-[var(--text)] leading-relaxed font-sans">
                      {block.value}
                    </p>
                  </div>
                );
              }

              if (block.type === 'table' && block.tableHeaders && block.tableRows) {
                return (
                  <div key={idx} className="overflow-x-auto border border-[var(--line)] rounded-xl bg-[var(--card-bg)] shadow-sm">
                    <table className="w-full text-left font-sans text-xs sm:text-sm">
                      <thead className="border-b border-[var(--line)] bg-[var(--bg)] font-mono text-xs uppercase tracking-wider text-[var(--text)]">
                        <tr>
                          {block.tableHeaders.map((header, hIdx) => (
                            <th key={hIdx} className="px-4 py-3 font-semibold">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--line)] text-[var(--muted)]">
                        {block.tableRows.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-[var(--bg)]/50 transition-colors">
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="px-4 py-3 font-mono text-xs leading-relaxed">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              }

              if (block.type === 'diagram') {
                if (block.diagramType === 'pipeline') {
                  return (
                    <div key={idx} className="p-5 rounded-xl border border-[var(--line)] bg-[#070A10] space-y-4 shadow-sm">
                      <div className="flex items-center justify-between font-mono text-xs text-slate-300 font-bold">
                        <span>SuperAgent Execution Pipeline Diagram</span>
                        <span className="text-[#6366f1]">6-Phase Harness</span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center font-mono text-xs">
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">1. PLAN</div>
                          <div className="text-[10px] text-slate-400">Goal → DAG</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">2. ROUTE</div>
                          <div className="text-[10px] text-slate-400">Vector DID Search</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">3. DISPATCH</div>
                          <div className="text-[10px] text-slate-400">Protocol Handler</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">4. VERIFY</div>
                          <div className="text-[10px] text-slate-400">Semantic Judge</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">5. NORMALIZE</div>
                          <div className="text-[10px] text-slate-400">Context State</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">6. RENDER</div>
                          <div className="text-[10px] text-slate-400">CanvasKit UI</div>
                        </div>
                      </div>
                    </div>
                  );
                }

                if (block.diagramType === 'bridge') {
                  return (
                    <div key={idx} className="p-5 rounded-xl border border-[var(--line)] bg-[#070A10] space-y-4 shadow-sm">
                      <div className="flex items-center justify-between font-mono text-xs text-slate-300 font-bold">
                        <span>Protocol Handler Pluggable Architecture</span>
                        <span className="text-emerald-400">Subclass AgentHandler</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">MCP / A2A / ACP</div>
                          <div className="text-[11px] text-slate-400">Built-in protocol handlers</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">LangGraph / n8n</div>
                          <div className="text-[11px] text-slate-400">Workflow engine bridges</div>
                        </div>
                        <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                          <div className="text-[#6366f1] font-bold">OpenAPI / Custom RPC</div>
                          <div className="text-[11px] text-slate-400">Community extensions</div>
                        </div>
                      </div>
                    </div>
                  );
                }
              }

              return null;
            })}
          </div>

          {/* Footer Navigation (Prev / Next) */}
          <div className="border-t border-[var(--line)] pt-6 flex flex-col sm:flex-row items-stretch gap-4 font-mono text-xs">
            {prevArticle && (
              <button
                onClick={() => handleArticleNav(prevArticle.id)}
                className="flex-1 flex items-center gap-3 p-4 rounded-xl border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] transition-all text-left text-[var(--muted)] hover:text-[var(--text)] group shadow-sm"
              >
                <ArrowLeft className="w-4 h-4 text-[#6366f1] flex-shrink-0 group-hover:-translate-x-1 transition-transform" />
                <div className="min-w-0">
                  <div className="text-[10px] text-[var(--faint)] uppercase">Previous</div>
                  <div className="font-semibold text-[var(--text)] truncate">{prevArticle.title}</div>
                </div>
              </button>
            )}

            {nextArticle && (
              <button
                onClick={() => handleArticleNav(nextArticle.id)}
                className="flex-1 flex items-center justify-end gap-3 p-4 rounded-xl border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] transition-all text-right text-[var(--muted)] hover:text-[var(--text)] group shadow-sm"
              >
                <div className="min-w-0">
                  <div className="text-[10px] text-[var(--faint)] uppercase">Next</div>
                  <div className="font-semibold text-[var(--text)] truncate">{nextArticle.title}</div>
                </div>
                <ArrowRight className="w-4 h-4 text-[#6366f1] flex-shrink-0 group-hover:translate-x-1 transition-transform" />
              </button>
            )}
          </div>

        </main>
      </div>

    </div>
  );
};
