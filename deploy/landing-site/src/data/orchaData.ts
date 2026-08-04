export interface TerminalLine {
  text: string;
  type?: 'cmd' | 'ok' | 'cm' | 'err' | 'out';
  delay?: number;
}

export const TERMINAL_LINES: TerminalLine[] = [
  { text: '$ uvx emerge init my-agent', type: 'cmd', delay: 800 },
  { text: '  ✓ scaffolded my-agent/  (emerge.yaml, server.py)', type: 'ok', delay: 600 },
  { text: '$ cd my-agent && uvx emerge run', type: 'cmd', delay: 800 },
  { text: '  ✓ serving on :3010', type: 'ok', delay: 500 },
  { text: '  ✓ registered → did:orcha:agent:my-agent', type: 'ok', delay: 700 },
  { text: '$ ./scripts/poc-e2e.sh', type: 'cmd', delay: 900 },
  { text: '  ⠿ register → goal → 3 protocols · verify · retry · settle', type: 'cm', delay: 800 },
  { text: '  ✓ POC: PROVEN', type: 'ok', delay: 0 },
];

export interface VerifiedRunAudit {
  runId: string;
  goal: string;
  timestamp: string;
  duration: string;
  runsVerified: string;
  cost: string;
  paymentMode: string;
  steps: {
    step: number;
    protocol: string;
    agent: string;
    verdict: string;
    cost: string;
    duration: string;
  }[];
}

export const VERIFIED_RUNS_DATA: VerifiedRunAudit[] = [
  {
    runId: 'run_20260727_e2e_01',
    goal: 'Show me my portfolio performance, use your web scraper agent to summarize en.wikipedia.org/wiki/Nvidia, and screenshot the dashboard',
    timestamp: '2026-07-27T05:12:00Z',
    duration: '13.2s',
    runsVerified: '5/5 runs verified',
    cost: '$0.00',
    paymentMode: 'mock',
    steps: [
      { step: 1, protocol: 'MCP', agent: 'finance-dashboard-agent', verdict: 'verified', cost: '$0.00', duration: '1.2s' },
      { step: 2, protocol: 'A2A', agent: 'web-scraper', verdict: 'verified', cost: '$0.00', duration: '3.4s' },
      { step: 3, protocol: 'COMPUTER_USE', agent: 'desktop-screenshot', verdict: 'verified', cost: '$0.00', duration: '2.8s' }
    ]
  },
  {
    runId: 'run_20260727_a2a_02',
    goal: 'Summarize https://en.wikipedia.org/wiki/Artificial_intelligence with the web scraper agent',
    timestamp: '2026-07-27T05:14:22Z',
    duration: '2.1s',
    runsVerified: '5/5 runs verified',
    cost: '$0.00',
    paymentMode: 'mock',
    steps: [
      { step: 1, protocol: 'A2A', agent: 'web-scraper', verdict: 'verified', cost: '$0.00', duration: '2.1s' }
    ]
  }
];

export interface ServiceDetail {
  port: string;
  name: string;
  protocol: string;
  description: string;
}

export const ARCHITECTURE_SERVICES: ServiceDetail[] = [
  {
    port: ':8000',
    name: 'Registry',
    protocol: 'REST + gRPC',
    description: 'Registration, manifests, and capability storage. Internal by design — Gateway owns auth.'
  },
  {
    port: ':8001',
    name: 'Planning & Discovery (PnD)',
    protocol: 'gRPC + pgvector',
    description: '3-tier gate (regex → MiniLM vector search → LLM classifier) and LLM DAG generator.'
  },
  {
    port: ':8002',
    name: 'SuperAgent Engine',
    protocol: 'LangGraph ReAct',
    description: 'LangGraph orchestration engine with 7-step execution pipeline, protocol adapters, checkpointing, and ExecutionObserver seam.'
  },
  {
    port: ':8080',
    name: 'Gateway Ingress',
    protocol: 'FastAPI / SSE',
    description: 'Public ingress with JWT auth, SSE run streaming, session state management, and mock payments.'
  },
  {
    port: ':3000',
    name: 'Frontend UI',
    protocol: 'React + CanvasKit',
    description: 'React SPA featuring the live CanvasKit renderer — where agent outputs become interactive visual dashboards.'
  }
];

export const ROADMAP_PHASES = [
  {
    version: 'v1 runtime',
    status: 'shipping',
    title: 'Multiprotocol orchestration',
    description: 'Registry, planner, SuperAgent, Gateway. MCP, A2A, and computer use in one run. Credential vault, human in the loop interrupts, mock payments, 7 example agents, emerge SDK, versioned emerge.yaml.',
    gate: 'fully local'
  },
  {
    version: 'v1.2 harness',
    status: 'next',
    title: 'Production grade reliability',
    description: 'DAG executor for parallel and dependent steps, output verification and semantic judging, retry and fallback policies, context management for long running tasks.',
    gate: 'after v1 adoption'
  },
  {
    version: 'network layer',
    status: 'aim',
    title: 'Peer discovery, fulfillment, reputation',
    description: 'Agents discover each other beyond a single registry; fulfillment is recorded through the ExecutionObserver seam. Experimental spikes ship labeled: gossip sidecar (node/) and FulfillmentRecorder.',
    gate: 'starts when one external agent registers'
  }
];

