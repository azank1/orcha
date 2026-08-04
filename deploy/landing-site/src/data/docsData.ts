export interface DocArticle {
  id: string;
  title: string;
  description: string;
  badge?: string;
  category: string;
  categoryName: string;
  readTime: string;
  content: {
    type: 'markdown' | 'code' | 'callout' | 'table' | 'diagram';
    value?: string;
    codeLanguage?: string;
    calloutType?: 'info' | 'warning' | 'tip' | 'success';
    calloutTitle?: string;
    tableHeaders?: string[];
    tableRows?: string[][];
    diagramType?: 'dag' | 'bridge' | 'pipeline';
  }[];
}

export interface DocCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  articles: DocArticle[];
}

export const DOCS_CATEGORIES: DocCategory[] = [
  {
    id: 'getting-started',
    name: 'Getting Started',
    icon: 'Rocket',
    description: 'Quick start guide, core philosophy, and 5-minute setup.',
    articles: [
      {
        id: 'overview',
        title: 'What is Orcha?',
        description: 'Orcha is an open-source, neutral runtime harness for multi-protocol AI agent orchestration.',
        category: 'getting-started',
        categoryName: 'Getting Started',
        readTime: '3 min read',
        content: [
          {
            type: 'markdown',
            value: `MCP, A2A, and ACP standardize how a message gets from point A to point B; they say nothing about how a dozen independently running agents get planned into one goal, called in order, authenticated, verified, and rendered into live UI.

That missing layer is an agent harness — and MCP, A2A, and Computer Use are just protocol bridges into it.

### Core Architecture Guarantee
Orcha adheres strictly to a 6-phase execution pipeline:
Plan → Route → Dispatch → Verify → Normalize → Render

Agents remain external, unopinionated, and protocol-agnostic. Orcha binds them together with cryptographic evidence, output verification, and live declarative UI.`
          },
          {
            type: 'callout',
            calloutType: 'info',
            calloutTitle: 'Harness vs. Agent',
            value: 'Orcha is not an AI model or a chatbot framework. It is the infrastructure harness that routes goals, manages credential vaults, handles retries, verifies outputs, and renders CanvasKit dashboards.'
          },
          {
            type: 'markdown',
            value: `### Key Principles

1. Protocol Agnostic: MCP, A2A, Computer Use, LangGraph, n8n, OpenAPI, gRPC — all treated as pluggable \`AgentHandler\` subclasses.
2. Declarative UI over Text: Instead of streaming raw text chat replies, Orcha returns interactive CanvasKit UI dashboards.
3. Verified Runs: Every run can be downloaded as a JSON evidence package with per-step verdicts, protocols, timings, and costs.
4. Local First: Runs 100% locally with \`PAYMENT_MODE=mock\` with zero closed external dependencies.`
          }
        ]
      },
      {
        id: 'quickstart',
        title: '5-Minute Quickstart',
        description: 'Initialize your first agent, launch the local stack, and run a multi-protocol goal.',
        category: 'getting-started',
        categoryName: 'Getting Started',
        readTime: '5 min read',
        content: [
          {
            type: 'markdown',
            value: `## Quickstart Guide

Get up and running with Orcha in under 5 minutes using \`uv\` / \`npm\` or Docker.`
          },
          {
            type: 'code',
            codeLanguage: 'bash',
            value: `# Clone the open-source repository
git clone https://github.com/solvent-metaorcha/orcha.git
cd orcha

# Install dependencies (Python + JS via uv & npm)
make install

# Generate Prisma database client & gRPC stubs
make prisma-generate
make grpc-generate

# Launch full local stack (Gateway, SuperAgent, Registry, Local Node)
./scripts/run-all.sh`
          },
          {
            type: 'markdown',
            value: `### Initialize a Custom Agent with emerge CLI

Use the \`emerge\` CLI tool to scaffold a new agent with a pre-configured \`emerge.yaml\` manifest:`
          },
          {
            type: 'code',
            codeLanguage: 'bash',
            value: `# Scaffold new agent directory
uvx emerge init my-search-agent

# Navigate and serve agent locally
cd my-search-agent
uvx emerge run

# Agent registers automatically against local registry:
# ✓ Registered → did:orcha:agent:my-search-agent
# ✓ Serving on http://localhost:3010`
          },
          {
            type: 'callout',
            calloutType: 'success',
            calloutTitle: 'Proof of Concept Verified',
            value: 'Run `./scripts/poc-e2e.sh` to execute an end-to-end multi-protocol test across MCP, A2A, and Computer Use in a single run.'
          }
        ]
      },
      {
        id: 'installation',
        title: 'System Requirements & Install',
        description: 'Detailed environment configuration, dependencies, and Docker setup.',
        category: 'getting-started',
        categoryName: 'Getting Started',
        readTime: '4 min read',
        content: [
          {
            type: 'markdown',
            value: `## Requirements & Installation

Orcha requires standard runtime environments for Python and TypeScript.`
          },
          {
            type: 'table',
            tableHeaders: ['Dependency', 'Version', 'Purpose'],
            tableRows: [
              ['Python', '>= 3.11', 'SuperAgent core runtime & protocol handlers'],
              ['Node.js', '>= 18.0', 'CanvasKit UI dashboard & Gateway proxy'],
              ['uv', 'Latest', 'Fast Python package management'],
              ['Prisma', '>= 5.0', 'Local state & execution logging database'],
              ['Docker (Optional)', '>= 24.0', 'Containerized full-stack deployment']
            ]
          },
          {
            type: 'markdown',
            value: `### Environment Variables

Configure your local environment using \`.env\`:`
          },
          {
            type: 'code',
            codeLanguage: 'env',
            value: `# Orcha Core Config
ORCHA_ENV=development
ORCHA_PORT=3000
REGISTRY_URL=http://localhost:3001
SUPERAGENT_URL=http://localhost:3002

# Settlement & Payment Mode
PAYMENT_MODE=mock # 'mock' or 'x402'

# Security & Vault
VAULT_KEY=orcha-dev-vault-secret-key-32bytes
DID_NAMESPACE=did:orcha:agent`
          }
        ]
      }
    ]
  },
  {
    id: 'architecture',
    name: 'Core Architecture',
    icon: 'Layers',
    description: 'Deep dive into SuperAgent, DAG planner, execution pipeline, and verifiers.',
    articles: [
      {
        id: 'superagent-pipeline',
        title: 'SuperAgent Execution Pipeline',
        description: 'How one natural language goal transforms into a verified, protocol-dispatched DAG graph.',
        category: 'architecture',
        categoryName: 'Core Architecture',
        readTime: '6 min read',
        content: [
          {
            type: 'markdown',
            value: `## SuperAgent Execution Pipeline

When a user submits a goal to Orcha, the SuperAgent acts as the top-level executor. It does not perform domain tasks directly; instead, it manages the workflow state machine.`
          },
          {
            type: 'diagram',
            diagramType: 'pipeline'
          },
          {
            type: 'markdown',
            value: `### Pipeline Phases

1. Goal Decomposition (Planner): Analyzes the prompt and breaks it into discrete sub-tasks with dependency links (DAG).
2. Agent Discovery & Routing: Queries the Registry using vector search and capability filters to match sub-tasks to registered DIDs (\`did:orcha:agent:*\`).
3. Protocol Dispatch: Routes each step to its corresponding protocol handler (\`MCPHandler\`, \`A2AHandler\`, \`ComputerUseHandler\`, \`LangGraphHandler\`, etc.).
4. Verification & Judging: Passes agent outputs through the \`ExecutionObserver\` for schema compliance and semantic quality check.
5. State Normalization: Aggregates verified outputs into a structured context window.
6. CanvasKit Rendering: Converts aggregated data into a declarative JSON layout for frontend visualization.`
          }
        ]
      },
      {
        id: 'goal-decomposition',
        title: 'DAG Goal Decomposition',
        description: 'Parallel and dependent step execution rules, retries, and fallback logic.',
        category: 'architecture',
        categoryName: 'Core Architecture',
        readTime: '5 min read',
        content: [
          {
            type: 'markdown',
            value: `## Directed Acyclic Graph (DAG) Execution

Complex goals often require sequential dependencies (e.g., fetch data before analyzing it) or independent steps that can run in parallel (e.g., scrape two sites at once).

### Example DAG Structure
For the goal: "Fetch portfolio holdings over MCP, summarize Nvidia news via A2A, and take a screenshot of the dashboard."`
          },
          {
            type: 'code',
            codeLanguage: 'json',
            value: `{
  "goal_id": "goal-9842",
  "nodes": [
    {
      "id": "step-1",
      "protocol": "MCP",
      "agent_did": "did:orcha:agent:finance-dashboard",
      "dependencies": []
    },
    {
      "id": "step-2",
      "protocol": "A2A",
      "agent_did": "did:orcha:agent:web-scraper",
      "dependencies": []
    },
    {
      "id": "step-3",
      "protocol": "COMPUTER_USE",
      "agent_did": "did:orcha:agent:desktop-screenshot",
      "dependencies": ["step-1", "step-2"]
    }
  ]
}`
          },
          {
            type: 'callout',
            calloutType: 'tip',
            calloutTitle: 'Parallel Dispatch',
            value: 'Steps 1 and 2 execute concurrently in parallel worker threads. Step 3 automatically waits until both Step 1 and Step 2 output verification checks pass.'
          }
        ]
      }
    ]
  },
  {
    id: 'bridges',
    name: 'Handlers & Protocol Bridges',
    icon: 'Cpu',
    description: 'Pluggable architecture for MCP, A2A, Computer Use, LangGraph, n8n, OpenAPI, and custom RPCs.',
    articles: [
      {
        id: 'protocol-overview',
        title: 'Pluggable Handler Architecture',
        description: 'Orcha handlers are completely pluggable and not restricted to a fixed protocol set.',
        category: 'bridges',
        categoryName: 'Handlers & Bridges',
        readTime: '4 min read',
        content: [
          {
            type: 'markdown',
            value: `## Pluggable Protocol Bridges

One of Orcha's core architectural advantages is that protocol support is open and extensible. 

Protocol handlers are subclasses of the base \`AgentHandler\` Python interface. You can write a bridge component for any agent framework or communication protocol:

- MCP (Model Context Protocol): Tool & resource server calls
- A2A (Agent-to-Agent): Autonomous HTTP/gRPC service-to-service communication
- Computer Use: OS-level mouse, keyboard, and display automation
- LangGraph & LangChain: Stateful multi-agent graph workflows
- n8n / Automations: Webhook & workflow engine triggers
- OpenAPI / REST: Direct HTTP API invocations
- gRPC / Custom RPCs: Low-latency binary RPC services`
          },
          {
            type: 'diagram',
            diagramType: 'bridge'
          }
        ]
      },
      {
        id: 'writing-custom-bridges',
        title: 'Writing a Custom Protocol Bridge',
        description: 'Step-by-step guide to adding a new protocol handler in under 50 lines of Python.',
        category: 'bridges',
        categoryName: 'Handlers & Bridges',
        readTime: '6 min read',
        content: [
          {
            type: 'markdown',
            value: `## How to Write a Custom Protocol Bridge

To create a bridge for a new protocol (e.g. \`LangGraph\`), follow this 3-step contract. No prior core team approval is needed.`
          },
          {
            type: 'markdown',
            value: `### Step 1: Subclass AgentHandler

Create a new handler file in \`services/superagent/src/superagent/handlers/langgraph_handler.py\`:`
          },
          {
            type: 'code',
            codeLanguage: 'python',
            value: `from superagent.handlers.base import AgentHandler
import requests

class LangGraphHandler(AgentHandler):
    """Bridge for orchestrating LangGraph multi-agent workflows."""
    
    def send_task(self, agent_manifest: dict, task_input: dict) -> str:
        endpoint = agent_manifest.get("endpoint")
        auth_token = self.get_vault_credential(agent_manifest["did"])
        
        try:
            response = requests.post(
                f"{endpoint}/threads/runs",
                json={"input": task_input},
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("output", "")
        except Exception as e:
            # Prefix fatal errors with Error: for verifier detection
            return f"Error: LangGraph execution failed - {str(e)}"`
          },
          {
            type: 'markdown',
            value: `### Step 2: Register Protocol in Dispatch Pipeline

Add your handler to \`middleware/pipeline.py\`:`
          },
          {
            type: 'code',
            codeLanguage: 'python',
            value: `if protocol == "LANGGRAPH":
    handler = LangGraphHandler(vault=self.vault)
    output = handler.send_task(manifest, step_input)`
          },
          {
            type: 'markdown',
            value: `### Step 3: Add Registry Adapter

Update \`emerge.yaml\` validation rules so \`protocol.type: LANGGRAPH\` passes schema checks.`
          },
          {
            type: 'callout',
            calloutType: 'success',
            calloutTitle: 'Contribute Your Bridge',
            value: 'Open a Pull Request with the branch name `feat/bridge-<protocol-slug>` (e.g., `feat/bridge-langgraph` or `feat/bridge-n8n`). Templates are located in `templates/your-first-bridge/`.'
          }
        ]
      }
    ]
  },
  {
    id: 'spec',
    name: 'emerge.yaml Specification',
    icon: 'FileText',
    description: 'The agent manifest specification, DIDs, capabilities, and governance.',
    articles: [
      {
        id: 'spec-overview',
        title: 'emerge.yaml Spec & Schema',
        description: 'Every agent in Orcha is declared via a versioned emerge.yaml manifest.',
        category: 'spec',
        categoryName: 'emerge.yaml Spec',
        readTime: '5 min read',
        content: [
          {
            type: 'markdown',
            value: `## emerge.yaml Manifest Specification

The \`emerge.yaml\` manifest is the standardized contract between agents and the Orcha registry. It defines the agent's identity, capabilities, protocol, and endpoints.

### Full Example Manifest`
          },
          {
            type: 'code',
            codeLanguage: 'yaml',
            value: `schema_version: "1.0"
did: "did:orcha:agent:finance-dashboard-agent"
name: "Finance Portfolio Tracker"
description: "Retrieves live equity holdings, crypto balances, and performance metrics over MCP"

protocol:
  type: "MCP" # Options: MCP | A2A | COMPUTER_USE | LANGGRAPH | N8N | OPENAPI | GRPC
  endpoint: "http://localhost:3010/mcp"
  transport: "sse"

capabilities:
  - name: "fetch_portfolio"
    description: "Returns holdings and total balance"
    parameters:
      user_id: "string"
      currency: "string"
  - name: "get_market_depth"
    description: "Returns orderbook depth"

auth:
  type: "bearer"
  vault_key_id: "FINANCE_AGENT_API_KEY"

output_format:
  renders_canvaskit: true
  schema_type: "json"`
          },
          {
            type: 'table',
            tableHeaders: ['Field', 'Type', 'Required', 'Description'],
            tableRows: [
              ['schema_version', 'string', 'Yes', 'Version of the emerge.yaml spec (e.g., "1.0")'],
              ['did', 'string', 'Yes', 'Decentralized Identifier in did:orcha:agent:* namespace'],
              ['name', 'string', 'Yes', 'Human-readable name of the agent'],
              ['protocol.type', 'string', 'Yes', 'Protocol bridge handler type'],
              ['capabilities', 'array', 'Yes', 'List of exposed function capabilities with parameters']
            ]
          }
        ]
      },
      {
        id: 'did-namespaces',
        title: 'DID Namespaces & Identity',
        description: 'Cryptographic identity rules for user agents and platform system tools.',
        category: 'spec',
        categoryName: 'emerge.yaml Spec',
        readTime: '3 min read',
        content: [
          {
            type: 'markdown',
            value: `## DID Namespaces

Orcha enforces strict Decentralized Identifier (DID) formatting to ensure agent identity security across registry lookups.`
          },
          {
            type: 'table',
            tableHeaders: ['Namespace', 'Target User', 'Example DID'],
            tableRows: [
              ['did:orcha:agent:*', 'External & Community Agents', 'did:orcha:agent:web-scraper-v1'],
              ['did:orcha:system:*', 'Platform System Core Tools', 'did:orcha:system:superagent-planner'],
              ['did:orcha:bridge:*', 'Protocol Bridge Adapters', 'did:orcha:bridge:langgraph-adapter']
            ]
          }
        ]
      }
    ]
  },
  {
    id: 'canvaskit',
    name: 'CanvasKit UI Engine',
    icon: 'Layout',
    description: 'Declarative JSON dashboard primitives replacing raw text chat replies.',
    articles: [
      {
        id: 'canvaskit-overview',
        title: 'Dashboards > Chat Bubbles',
        description: 'Why Orcha renders rich interactive dashboards instead of streaming text replies.',
        category: 'canvaskit',
        categoryName: 'CanvasKit UI Engine',
        readTime: '4 min read',
        content: [
          {
            type: 'markdown',
            value: `## CanvasKit UI Rendering Engine

When complex agents complete tasks (e.g. financial analysis or system monitoring), a text chat reply like "Here are your 15 numbers..." is slow and painful to digest.

Orcha agents return CanvasKit JSON UI manifests, which the frontend automatically compiles into live, interactive visual dashboards.`
          },
          {
            type: 'code',
            codeLanguage: 'json',
            value: `{
  "version": "1.0",
  "title": "Portfolio Performance Dashboard",
  "layout": "dashboard",
  "components": [
    {
      "type": "metric_card",
      "id": "card-1",
      "label": "Total Portfolio Value",
      "value": 142300,
      "unit": "USD",
      "delta": 4.8,
      "trend": "up"
    },
    {
      "type": "line_chart",
      "id": "chart-1",
      "label": "7-Day Performance",
      "data": [
        {"x": "Mon", "y": 136000},
        {"x": "Tue", "y": 138500},
        {"x": "Wed", "y": 142300}
      ]
    }
  ]
}`
          }
        ]
      }
    ]
  },
  {
    id: 'sdk-cli',
    name: 'CLI & SDK Reference',
    icon: 'Terminal',
    description: 'Developer commands, Python SDK methods, and programmatic orchestration.',
    articles: [
      {
        id: 'cli-commands',
        title: 'CLI Reference (emerge)',
        description: 'Complete command-line interface documentation for agent developers.',
        category: 'sdk-cli',
        categoryName: 'CLI & SDK Reference',
        readTime: '4 min read',
        content: [
          {
            type: 'markdown',
            value: `## emerge CLI Reference

The \`emerge\` CLI provides scaffolding, running, and validation tools.`
          },
          {
            type: 'code',
            codeLanguage: 'bash',
            value: `# Scaffold a new agent directory
uvx emerge init <agent-slug>

# Run and serve agent locally
uvx emerge run --port 3010

# Validate agent emerge.yaml manifest against schema
uvx emerge validate emerge.yaml

# Test dispatch against a running agent
uvx emerge dispatch --did did:orcha:agent:my-agent --input '{"query": "test"}'

# List all agents registered in local Orcha node
uvx emerge registry list`
          }
        ]
      },
      {
        id: 'python-sdk',
        title: 'Python SDK Usage',
        description: 'Programmatically trigger goal orchestration in Python applications.',
        category: 'sdk-cli',
        categoryName: 'CLI & SDK Reference',
        readTime: '3 min read',
        content: [
          {
            type: 'markdown',
            value: `## Python SDK (\`emerge\` package)

Integrate Orcha orchestration directly into Python backend services.`
          },
          {
            type: 'code',
            codeLanguage: 'python',
            value: `from emerge import OrchaClient

# Initialize client pointing to local Orcha Gateway
client = OrchaClient(gateway_url="http://localhost:3000")

# Submit natural language goal
result = client.orchestrate(
    goal="Summarize Nvidia earnings and update finance dashboard",
    payment_mode="mock"
)

print(f"Goal Status: {result.status}")
print(f"Verified Steps: {len(result.verified_steps)}")
print(f"CanvasKit UI Manifest: {result.canvas_ui}")`
          }
        ]
      }
    ]
  }
];
