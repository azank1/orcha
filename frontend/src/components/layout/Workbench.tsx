import { useState } from 'react'
import { cn } from '../ui/cn'
import { RunTab } from '../workbench/RunTab'
import { TraceTab } from '../workbench/TraceTab'
import { KeysTab } from '../workbench/KeysTab'
import { AgentsTab } from '../workbench/AgentsTab'

type WorkbenchTab = 'Run' | 'Trace' | 'Keys' | 'Agents'
const TABS: WorkbenchTab[] = ['Run', 'Trace', 'Keys', 'Agents']

/** Developer-mode workbench: run inspector, live trace, BYOK console, agents. */
export function Workbench() {
  const [activeTab, setActiveTab] = useState<WorkbenchTab>('Run')

  return (
    <>
      {/* Tab bar */}
      <div className="flex items-center gap-1 px-2 py-1.5 bg-surface-elevated border-b border-surface-border shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            aria-selected={activeTab === tab}
            role="tab"
            className={cn(
              'flex-1 h-8 rounded-sm font-mono text-[11px] transition-colors duration-150',
              activeTab === tab
                ? 'bg-brand-primary-dim text-brand-primary-light font-medium'
                : 'text-text-secondary hover:text-text-body',
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin py-3">
        {activeTab === 'Run' && <RunTab />}
        {activeTab === 'Trace' && <TraceTab />}
        {activeTab === 'Keys' && <KeysTab />}
        {activeTab === 'Agents' && <AgentsTab />}
      </div>
    </>
  )
}
