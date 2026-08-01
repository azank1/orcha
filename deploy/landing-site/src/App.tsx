import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { ValuePropGrid } from './components/ValuePropGrid';
import { CanvasKitShowcase } from './components/CanvasKitShowcase';
import { SDKAndManifest } from './components/SDKAndManifest';
import { VerifiedRunsSection } from './components/VerifiedRunsSection';
import { ProofCards } from './components/ProofCards';
import { FleetGrid } from './components/FleetGrid';
import { InteractiveDAGArchitecture } from './components/InteractiveDAGArchitecture';
import { RoadmapAndNonGoals } from './components/RoadmapAndNonGoals';
import { ContributionSection } from './components/ContributionSection';
import { DocumentationPage } from './components/DocumentationPage';
import { ProtocolSlideshow } from './components/ProtocolSlideshow';
import { ScrollReveal } from './components/ScrollReveal';
import { Footer } from './components/Footer';
import { Terminal, BookOpen, ArrowRight, Layers, Cpu, ShieldCheck } from 'lucide-react';
import { SANDBOX_URL, SANDBOX_HOST } from './config/sandbox';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
  }, [theme]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [activeTab]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] flex flex-col font-sans selection:bg-[#6366f1] selection:text-white transition-colors duration-200">
      <div className="grain-overlay" aria-hidden="true" />
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {/* OVERVIEW TAB (Home Page) */}
        {activeTab === 'overview' && (
          <div className="space-y-16 pb-16">
            <ScrollReveal direction="none" duration={0.6}>
              <HeroSection
                onLaunchSandbox={() => window.open(SANDBOX_URL, '_blank', 'noopener')}
                onExploreDocs={() => setActiveTab('docs')}
              />
            </ScrollReveal>

            <ScrollReveal direction="up" delay={0.1}>
              <ValuePropGrid />
            </ScrollReveal>

            {/* Protocol Showcase Slideshow */}
            <ScrollReveal direction="up" delay={0.15}>
              <ProtocolSlideshow />
            </ScrollReveal>

            {/* Live sandbox embed */}
            <ScrollReveal direction="up" delay={0.25}>
              <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="rounded-2xl border border-[var(--line)] bg-[var(--card-bg)] overflow-hidden shadow-sm">
                  <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--line)] font-mono text-xs">
                    <span className="text-[var(--text)] font-semibold uppercase tracking-wider">run it live</span>
                    <span className="text-[var(--faint)]">{SANDBOX_HOST} — real runs, real verdicts</span>
                  </div>
                  <iframe
                    src={SANDBOX_URL}
                    title="Orcha live sandbox"
                    className="w-full h-[640px] bg-[#0b0b0e]"
                    loading="lazy"
                  />
                </div>
              </section>
            </ScrollReveal>

            {/* Sandbox Teaser Card */}
            <ScrollReveal direction="up" delay={0.2}>
              <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="p-6 sm:p-8 rounded-2xl border border-[var(--line)] bg-[var(--card-bg)] flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
                  <div className="space-y-2 max-w-2xl">
                    <div className="font-mono text-xs text-[#6366f1] uppercase font-bold tracking-wider flex items-center gap-2">
                      <Terminal className="w-4 h-4" />
                      Interactive Multiprotocol Sandbox
                    </div>
                    <h3 className="font-display font-bold text-xl sm:text-2xl text-[var(--text)]">
                      Run a real goal on the live sandbox
                    </h3>
                    <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed">
                      Guest access, no signup: pick a model, run a goal across MCP, A2A, and computer use, watch every step verify, download the run audit. 2 goals per guest on hosted free-tier models.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <a
                      href={SANDBOX_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group font-mono text-xs font-semibold pl-5 pr-2 py-2 rounded-full bg-[#6366f1] text-white hover:bg-[#4f52c8] transition-all flex items-center gap-3 shadow-md"
                    >
                      <span className="block overflow-hidden h-[1em]">
                        <span className="flex flex-col leading-[1em] transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                          <span>Open the live sandbox</span>
                          <span>Open the live sandbox</span>
                        </span>
                      </span>
                      <span className="w-7 h-7 rounded-full bg-white flex items-center justify-center transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:rotate-[-45deg]">
                        <ArrowRight className="w-3.5 h-3.5 text-[#6366f1]" />
                      </span>
                    </a>
                    <button
                      onClick={() => setActiveTab('docs')}
                      className="font-mono text-xs font-semibold px-5 py-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] text-[var(--text)] hover:border-[#6366f1] transition-all flex items-center gap-2"
                    >
                      <BookOpen className="w-4 h-4 text-[#6366f1]" />
                      Read System Docs
                    </button>
                  </div>
                </div>
              </section>
            </ScrollReveal>

            <ScrollReveal direction="up" delay={0.1}>
              <InteractiveDAGArchitecture />
            </ScrollReveal>

            <ScrollReveal direction="up">
              <VerifiedRunsSection />
            </ScrollReveal>

            <ScrollReveal direction="up" delay={0.1}>
              <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <FleetGrid />
              </section>
            </ScrollReveal>

            <ScrollReveal direction="up" delay={0.1}>
              <ProofCards />
            </ScrollReveal>
            
            {/* Fancy Roadmap Section */}
            <ScrollReveal direction="up" delay={0.1}>
              <RoadmapAndNonGoals />
            </ScrollReveal>
            
            {/* Fancy Contribution Section */}
            <ScrollReveal direction="up" delay={0.1}>
              <ContributionSection />
            </ScrollReveal>
          </div>
        )}

        {/* DOCUMENTATION SUBPAGE TAB */}
        {activeTab === 'docs' && (
          <ScrollReveal direction="none" duration={0.4}>
            <DocumentationPage onNavigateToTab={(tab) => setActiveTab(tab)} />
          </ScrollReveal>
        )}

        {/* STANDALONE FANCY ROADMAP TAB */}
        {activeTab === 'roadmap' && (
          <div className="py-12">
            <ScrollReveal direction="up">
              <RoadmapAndNonGoals />
            </ScrollReveal>
          </div>
        )}

        {/* STANDALONE FANCY CONTRIBUTING TAB */}
        {activeTab === 'contributing' && (
          <div className="py-12">
            <ScrollReveal direction="up">
              <ContributionSection />
            </ScrollReveal>
          </div>
        )}
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

