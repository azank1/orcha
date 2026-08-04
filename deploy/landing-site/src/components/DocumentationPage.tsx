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
    'getting-started': <Rocket className="w-4 h-4 text-[var(--ink)]" />,
    architecture: <Layers className="w-4 h-4 text-[var(--ink)]" />,
    bridges: <Cpu className="w-4 h-4 text-[var(--ink)]" />,
    spec: <FileText className="w-4 h-4 text-[var(--ink)]" />,
    canvaskit: <Layout className="w-4 h-4 text-[var(--ink)]" />,
    'sdk-cli': <Terminal className="w-4 h-4 text-[var(--ink)]" />
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
    <div className="min-h-[calc(100vh-3.5rem)] bg-[var(--paper)] text-[var(--ink)] transition-colors">
      
      {/* Docs Header Banner */}
      <div className="border-b border-black/10 bg-white/60 py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--ink)]">
              Developer Docs
            </h1>
            <p className="font-mono text-xs text-[var(--muted-light)]">
              architecture · spec · sdk
            </p>
          </div>

          {/* Quick Search Input */}
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted-light)]" />
            <input
              type="text"
              placeholder="Search docs, APIs, specs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-black/10 focus:border-black/40 rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-[var(--ink)] placeholder:text-[var(--muted-light)] outline-none transition-all shadow-sm"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs font-mono text-[var(--muted-light)] hover:text-[var(--ink)]"
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
        <aside className="lg:w-72 flex-shrink-0 border-b lg:border-b-0 lg:border-r border-black/10 bg-white px-4 sm:px-6 py-8 space-y-6">
          <div className="sticky top-20 space-y-6">
            
            {/* Navigation Categories */}
            <nav className="space-y-6 max-h-[calc(100vh-10rem)] overflow-y-auto pr-2 custom-scrollbar">
              {filteredCategories.length === 0 ? (
                <div className="text-xs font-mono text-[var(--muted-light)] p-3 border border-dashed border-black/10 rounded-lg">
                  No matching doc articles found for "{searchQuery}".
                </div>
              ) : (
                filteredCategories.map((cat) => (
                  <div key={cat.id} className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-[var(--ink)] uppercase tracking-wider px-2">
                      {categoryIconMap[cat.id] || <BookOpen className="w-4 h-4 text-[var(--ink)]" />}
                      <span>{cat.name}</span>
                    </div>

                    <div className="space-y-0.5 border-l border-black/10 ml-2.5 pl-2.5">
                      {cat.articles.map((art) => {
                        const isActive = art.id === selectedArticleId;
                        return (
                          <button
                            key={art.id}
                            onClick={() => setSelectedArticleId(art.id)}
                            className={`w-full text-left px-2.5 py-1.5 rounded-md font-mono text-xs transition-all flex items-center justify-between group ${
                              isActive
                                ? 'bg-[var(--ink)] text-white font-semibold shadow-sm'
                                : 'text-[var(--muted-light)] hover:text-[var(--ink)] hover:bg-black/5'
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
            <div className="p-4 rounded-xl border border-black/10 bg-white space-y-2.5 font-mono text-xs shadow-sm">
              <div className="font-bold text-[var(--ink)] flex items-center justify-between">
                <span>Core Links</span>
                <span className="w-2 h-2 rounded-full bg-[var(--ink)]"></span>
              </div>
              <div className="space-y-1.5 text-[var(--muted-light)]">
                {onNavigateToTab && (
                  <>
                    <button
                      onClick={() => onNavigateToTab('roadmap')}
                      className="block w-full text-left hover:text-[var(--ink)] transition-colors flex items-center justify-between py-1"
                    >
                      <span>Interactive Roadmap</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onNavigateToTab('contributing')}
                      className="block w-full text-left hover:text-[var(--ink)] transition-colors flex items-center justify-between py-1"
                    >
                      <span>Bridge Contributor Guide</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => onNavigateToTab('playground')}
                      className="block w-full text-left hover:text-[var(--ink)] transition-colors flex items-center justify-between py-1"
                    >
                      <span>Execution Sandbox</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </>
                )}
                <a
                  href="https://github.com/solvent-metaorcha/orcha"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block hover:text-[var(--ink)] transition-colors flex items-center justify-between py-1"
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
          <div className="border-b border-black/10 pb-6 space-y-3">
            <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
              <span className="text-[var(--ink)] font-semibold">{currentArticle.categoryName}</span>
              <span className="text-[var(--muted-light)]">/</span>
              <span className="text-[var(--muted-light)]">{currentArticle.title}</span>
              <span className="ml-auto text-[11px] text-[var(--muted-light)] bg-white px-2 py-0.5 rounded border border-black/10">
                {currentArticle.readTime}
              </span>
            </div>

            <h2 className="font-display font-bold text-2xl sm:text-3xl text-[var(--ink)] tracking-tight">
              {currentArticle.title}
            </h2>

            <p className="text-sm text-[var(--muted-light)] leading-relaxed">
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
                    className="prose dark:prose-invert max-w-none text-xs sm:text-sm text-[var(--ink)] leading-relaxed space-y-3"
                  >
                    {block.value?.split('\n\n').map((paragraph, pIdx) => {
                      if (paragraph.startsWith('## ')) {
                        return (
                          <h3 key={pIdx} className="font-display font-bold text-xl text-[var(--ink)] mt-6 mb-2 tracking-tight">
                            {paragraph.replace('## ', '')}
                          </h3>
                        );
                      }
                      if (paragraph.startsWith('### ')) {
                        return (
                          <h4 key={pIdx} className="font-display font-bold text-base text-[var(--ink)] mt-4 mb-2">
                            {paragraph.replace('### ', '')}
                          </h4>
                        );
                      }
                      if (paragraph.startsWith('1. ') || paragraph.startsWith('- ')) {
                        const items = paragraph.split('\n');
                        return (
                          <ul key={pIdx} className="space-y-1.5 my-2 pl-4 list-disc text-[var(--muted-light)]">
                            {items.map((item, iIdx) => (
                              <li key={iIdx} className="leading-relaxed">
                                {item.replace(/^[0-9]+\.\s+|^-\s+/, '')}
                              </li>
                            ))}
                          </ul>
                        );
                      }
                      return (
                        <p key={pIdx} className="text-[var(--muted-light)] leading-relaxed">
                          {paragraph}
                        </p>
                      );
                    })}
                  </div>
                );
              }

              if (block.type === 'code') {
                return (
                  <div key={idx} className="relative group rounded-xl overflow-hidden border border-[var(--line-dark)] bg-[#050505] shadow-sm">
                    {/* Header bar */}
                    <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--line-dark)] bg-[#0a0a0a] font-mono text-[11px] text-[var(--muted-dark)]">
                      <div className="flex items-center gap-2">
                        <Code className="w-3.5 h-3.5" />
                        <span className="uppercase">{block.codeLanguage || 'code'}</span>
                      </div>
                      <button
                        onClick={() => handleCopy(block.value || '', idx)}
                        className="flex items-center gap-1.5 text-[var(--muted-dark)] hover:text-white transition-colors py-0.5 px-2 rounded hover:bg-white/10"
                      >
                        {copiedCodeIndex === idx ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-[var(--ok)]" />
                            <span className="text-[var(--ok)] font-semibold">Copied</span>
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
                    <pre className="p-4 font-mono text-xs text-neutral-200 overflow-x-auto leading-relaxed custom-scrollbar">
                      <code>{block.value}</code>
                    </pre>
                  </div>
                );
              }

              if (block.type === 'callout') {
                const calloutStyles = {
                  info: 'border-black/20 bg-black/5 text-[var(--ink)]',
                  warning: 'border-black/20 bg-black/5 text-[var(--muted-light)]',
                  tip: 'border-black/20 bg-black/5 text-[var(--ink)]',
                  success: 'border-[var(--ok)]/40 bg-[var(--ok)]/5 text-[var(--ok)]'
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
                    <p className="text-xs sm:text-sm text-[var(--ink)] leading-relaxed">
                      {block.value}
                    </p>
                  </div>
                );
              }

              if (block.type === 'table' && block.tableHeaders && block.tableRows) {
                return (
                  <div key={idx} className="overflow-x-auto border border-black/10 rounded-xl bg-white shadow-sm">
                    <table className="w-full text-left text-xs sm:text-sm">
                      <thead className="border-b border-black/10 bg-[var(--paper)] font-mono text-xs uppercase tracking-wider text-[var(--ink)]">
                        <tr>
                          {block.tableHeaders.map((header, hIdx) => (
                            <th key={hIdx} className="px-4 py-3 font-semibold">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black/10 text-[var(--muted-light)]">
                        {block.tableRows.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-black/5 transition-colors">
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
                    <div key={idx} className="p-5 rounded-xl border border-[var(--line-dark)] bg-[#050505] space-y-4 shadow-sm">
                      <div className="flex items-center justify-between font-mono text-xs text-neutral-300 font-bold">
                        <span>SuperAgent Execution Pipeline Diagram</span>
                        <span className="text-white">6-Phase Harness</span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center font-mono text-xs">
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">1. PLAN</div>
                          <div className="text-[10px] text-[var(--muted-dark)]">Goal → DAG</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">2. ROUTE</div>
                          <div className="text-[10px] text-[var(--muted-dark)]">Vector DID Search</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">3. DISPATCH</div>
                          <div className="text-[10px] text-[var(--muted-dark)]">Protocol Handler</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">4. VERIFY</div>
                          <div className="text-[10px] text-[var(--muted-dark)]">Semantic Judge</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">5. NORMALIZE</div>
                          <div className="text-[10px] text-[var(--muted-dark)]">Context State</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">6. RENDER</div>
                          <div className="text-[10px] text-[var(--muted-dark)]">CanvasKit UI</div>
                        </div>
                      </div>
                    </div>
                  );
                }

                if (block.diagramType === 'bridge') {
                  return (
                    <div key={idx} className="p-5 rounded-xl border border-[var(--line-dark)] bg-[#050505] space-y-4 shadow-sm">
                      <div className="flex items-center justify-between font-mono text-xs text-neutral-300 font-bold">
                        <span>Protocol Handler Pluggable Architecture</span>
                        <span className="text-white">Subclass AgentHandler</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">MCP / A2A / ACP</div>
                          <div className="text-[11px] text-[var(--muted-dark)]">Built-in protocol handlers</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">LangGraph / n8n</div>
                          <div className="text-[11px] text-[var(--muted-dark)]">Workflow engine bridges</div>
                        </div>
                        <div className="p-3 rounded bg-white/5 border border-[var(--line-dark)] space-y-1">
                          <div className="text-white font-bold">OpenAPI / Custom RPC</div>
                          <div className="text-[11px] text-[var(--muted-dark)]">Community extensions</div>
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
          <div className="border-t border-black/10 pt-6 flex flex-col sm:flex-row items-stretch gap-4 font-mono text-xs">
            {prevArticle && (
              <button
                onClick={() => handleArticleNav(prevArticle.id)}
                className="flex-1 flex items-center gap-3 p-4 rounded-xl border border-black/10 bg-white hover:border-black/40 transition-all text-left text-[var(--muted-light)] hover:text-[var(--ink)] group shadow-sm"
              >
                <ArrowLeft className="w-4 h-4 text-[var(--ink)] flex-shrink-0 group-hover:-translate-x-1 transition-transform" />
                <div className="min-w-0">
                  <div className="text-[10px] text-[var(--muted-light)] uppercase">Previous</div>
                  <div className="font-semibold text-[var(--ink)] truncate">{prevArticle.title}</div>
                </div>
              </button>
            )}

            {nextArticle && (
              <button
                onClick={() => handleArticleNav(nextArticle.id)}
                className="flex-1 flex items-center justify-end gap-3 p-4 rounded-xl border border-black/10 bg-white hover:border-black/40 transition-all text-right text-[var(--muted-light)] hover:text-[var(--ink)] group shadow-sm"
              >
                <div className="min-w-0">
                  <div className="text-[10px] text-[var(--muted-light)] uppercase">Next</div>
                  <div className="font-semibold text-[var(--ink)] truncate">{nextArticle.title}</div>
                </div>
                <ArrowRight className="w-4 h-4 text-[var(--ink)] flex-shrink-0 group-hover:translate-x-1 transition-transform" />
              </button>
            )}
          </div>

        </main>
      </div>

    </div>
  );
};
