import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { SplitHero } from './components/SplitHero';
import { Manifesto } from './components/Manifesto';
import { PipelineStrip } from './components/PipelineStrip';
import { PluginDirectory } from './components/PluginDirectory';
import { PluginDetailPage } from './components/PluginDetailPage';
import { ObservationSection } from './components/ObservationSection';
import { ProtocolRing } from './components/ProtocolRing';
import { SandboxDock } from './components/SandboxDock';
import { ValuePropGrid } from './components/ValuePropGrid';
import { InteractiveDAGArchitecture } from './components/InteractiveDAGArchitecture';
import { SDKAndManifest } from './components/SDKAndManifest';
import { RoadmapAndNonGoals } from './components/RoadmapAndNonGoals';
import { ContributionSection } from './components/ContributionSection';
import { DocumentationPage } from './components/DocumentationPage';
import { ScrollReveal } from './components/ScrollReveal';
import { Footer } from './components/Footer';

const ScrollManager: React.FC = () => {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      const id = hash.slice(1);
      requestAnimationFrame(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'auto', block: 'start' });
      });
    } else {
      window.scrollTo({ top: 0 });
    }
  }, [pathname, hash]);
  return null;
};

const BridgeRedirect: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  return <Navigate to={`/plugins/${slug ?? ''}`} replace />;
};

const Home: React.FC = () => (
  <>
    <SplitHero />
    <ScrollReveal direction="up">
      <Manifesto />
    </ScrollReveal>
    <PipelineStrip />
    <ScrollReveal direction="up">
      <PluginDirectory />
    </ScrollReveal>
    <ScrollReveal direction="up">
      <ValuePropGrid />
    </ScrollReveal>
    <ObservationSection />
    <ScrollReveal direction="up">
      <InteractiveDAGArchitecture />
    </ScrollReveal>
    <ProtocolRing />
    <ScrollReveal direction="up">
      <SDKAndManifest />
    </ScrollReveal>
  </>
);

export default function App() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--fg)] flex flex-col selection:bg-white selection:text-black">
      <div className="grain-overlay" aria-hidden="true" />
      <ScrollManager />
      <Navbar />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/plugins/:slug" element={<PluginDetailPage />} />
          <Route path="/bridges/:slug" element={<BridgeRedirect />} />
          <Route
            path="/docs"
            element={
              <DocumentationPage
                onNavigateToTab={(tab) =>
                  navigate(tab === 'docs' ? '/docs' : tab === 'roadmap' ? '/roadmap' : tab === 'contributing' ? '/contributing' : '/')
                }
              />
            }
          />
          <Route path="/roadmap" element={<RoadmapAndNonGoals />} />
          <Route path="/contributing" element={<ContributionSection />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>

      <Footer />
      <SandboxDock />
    </div>
  );
}
