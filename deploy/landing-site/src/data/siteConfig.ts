// Site content — ported from the launch-kit config (kimi files/, orcha-internal).
// All GitHub URLs point at the org. Keep copy terse and factual (docs/design.md §7).

export const GITHUB_URL = 'https://github.com/solvent-metaorcha/orcha';
export const DISCORD_URL = 'https://discord.gg/26d9ytRTM';

export interface BridgeItem {
  slug: string;
  name: string;
  code: string;
  logo: 'mcp' | 'a2a' | 'computer-use' | 'canvaskit';
  clip: string;
  address: string;
  status: string;
  handler: string;
  stack: string;
  ctaText: string;
  ctaHref: string;
  glyphs: string;
  article: { title: string; paragraphs: string[] };
}

export const site = {
  title: 'Orcha — Many Models. One Harness.',
  description:
    'Many models, one harness. Orcha is an open-source runtime for multi-protocol agent orchestration — one goal in, a verified multi-agent run out.',
};

export const nav = {
  links: [
    { label: 'Bridges', href: '/#plugins' },
    { label: 'Sandbox', href: '/#observation' },
    { label: 'Protocols', href: '/#protocols' },
    { label: 'Docs', href: '/docs' },
  ],
};

export const hero = {
  titleLines: ['Many models.', 'One harness.'],
  leadText:
    'Models are converging — the gap between the best of them is a few points and shrinking. What makes an agent dependable is everything around the model: planning, routing, identity, verification. Orcha is that layer, open and inspectable.',
};

export const manifesto = {
  text: 'Models commoditize; harnesses decide. Orcha is neutral ground between agents. A natural-language goal enters a three-tier gate — auth, DID and scope verification — then a SuperAgent planner (LLM + pgvector) decomposes it into a DAG and dispatches each step across MCP, A2A and computer-use agents. Every step returns a verdict. Every run exports an audit: per-step agent, protocol, cost and timing. Agents stay external and independent — no glue code, no chat bubbles. Outputs come back as declarative CanvasKit manifests and render as live dashboards. Today\'s harness is neutral ground; tomorrow it\'s where agents find and check each other\'s work.',
};

export const bridges: BridgeItem[] = [
  {
    slug: 'mcp',
    name: 'MCP',
    code: '01',
    logo: 'mcp',
    clip: 'plugin-mcp',
    address: 'Tools & Resources · SSE + stdio transports',
    status: 'Capabilities harvested from the live endpoint at registration',
    handler: 'services/superagent/src/superagent/handlers/mcp_handler.py',
    stack: 'Python 3.11 · credential vault + auth cascade',
    ctaText: 'Read the handler',
    ctaHref: `${GITHUB_URL}/tree/main/services/superagent/src/superagent/handlers`,
    glyphs: ' .:-=+*#%@',
    article: {
      title: 'Bridge 01 — MCP: tools and resources',
      paragraphs: [
        'The tool servers everyone already runs, composed into the run. The MCP handler speaks SSE and stdio, harvests capabilities from the live endpoint at registration, and routes every call through the credential vault with an auth cascade.',
        'await handler.call_tool(agent_id="did:orcha:agent:finance-dashboard", capability_id="get_portfolio_dashboard", args={}, transport=transport) — one uniform call shape regardless of what ships underneath.',
        "The harness doesn't care what protocol comes next. MCP is simply the first bridge: a subclass of AgentHandler, registered in middleware/pipeline.py, dispatch-mapped in emerge.yaml.",
      ],
    },
  },
  {
    slug: 'a2a',
    name: 'A2A',
    code: '02',
    logo: 'a2a',
    clip: 'plugin-a2a',
    address: 'Agent-to-Agent · plus ACP alias route',
    status: 'Verified handoffs between independent agents',
    handler: 'services/superagent/src/superagent/handlers/a2a_handler.py',
    stack: 'gRPC · task payloads as dicts, strings back',
    ctaText: 'Read the handler',
    ctaHref: `${GITHUB_URL}/tree/main/services/superagent/src/superagent/handlers`,
    glyphs: ' .·:;+x%#@',
    article: {
      title: 'Bridge 02 — A2A: agent-to-agent handoffs',
      paragraphs: [
        'A2A lets specialised agents stay external and independent while the SuperAgent composes them into one run. A web-scraper agent can summarise a page while a finance agent builds a dashboard — same goal, same audit.',
        'The bridge also carries an ACP alias route, so agents speaking adjacent protocols dispatch through the same pipeline without bespoke glue.',
        'Every handoff is observed: the ExecutionObserver seam records which agent ran, on which protocol, for how long, at what cost — and whether the step verified.',
      ],
    },
  },
  {
    slug: 'computer-use',
    name: 'Computer-Use',
    code: '03',
    logo: 'computer-use',
    clip: 'plugin-computer-use',
    address: 'Screens + Input · desktop control',
    status: 'Screenshot artifacts captured per step',
    handler: 'services/superagent/src/superagent/handlers/computer_use_handler.py',
    stack: 'Live browser + desktop sessions',
    ctaText: 'Read the handler',
    ctaHref: `${GITHUB_URL}/tree/main/services/superagent/src/superagent/handlers`,
    glyphs: ' ░▒▓█',
    article: {
      title: 'Bridge 03 — Computer-Use: screens and input',
      paragraphs: [
        'When no API exists, an agent drives the machine itself. The computer-use bridge captures screens and issues input, so a run can end with a real screenshot artifact of a live dashboard — not a promise that one exists.',
        'Computer-use steps are captured as screenshot artifacts inside the evidence package, side by side with MCP tool calls and A2A handoffs.',
        'This is the third bridge in the v1 runtime. The dispatch table is open: LangGraph, OpenAPI, gRPC or a custom RPC can become a handler in under fifty lines of Python.',
      ],
    },
  },
  {
    slug: 'canvaskit',
    name: 'CanvasKit',
    code: '04',
    logo: 'canvaskit',
    clip: 'plugin-canvaskit',
    address: 'Declarative UI manifests · React :3000',
    status: 'Metric cards, charts, tables — rendered live',
    handler: 'frontend/src/components/canvas/',
    stack: 'React SPA · CanvasKit renderer',
    ctaText: 'See the renderer',
    ctaHref: `${GITHUB_URL}/tree/main/frontend/src/components/canvas`,
    glyphs: ' ◇◈○●◐◑',
    article: {
      title: 'Output 04 — CanvasKit: manifests, not chat bubbles',
      paragraphs: [
        'Agents return declarative CanvasKit manifests, and the frontend renders them as interactive visual dashboards — metric cards, charts and tables, live as the run completes.',
        'The renderer is a set of dashboard primitives under frontend/src/components/canvas/. Building new primitives is one of the highest-leverage ways to grow the ecosystem.',
        'A portfolio step returns numbers; CanvasKit returns a dashboard. The audit records both, so what the user saw is exactly what the run produced.',
      ],
    },
  },
];

export const observation = {
  sectionLabel: 'Run it live — sandbox.metaorcha.ai',
  statusText: 'live',
};

export const footer = {
  copyrightText: '© 2026 Orcha · Apache 2.0',
};
