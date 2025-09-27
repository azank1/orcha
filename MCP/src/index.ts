import express from 'express';
import { rpcHandler } from './rpc.js';
import { tools } from './tools.js';

const app = express();
app.use(express.json({ limit: '1mb' }));

app.get('/healthz', (_req, res) => res.json({ ok: true, service: 'MCP', version: '0.1.0' }));
app.get('/.well-known/mcp/tools', (_req, res) => res.json({ tools }));
app.post('/rpc', rpcHandler);

const PORT = process.env.PORT ? Number(process.env.PORT) : 9090;
app.listen(PORT, () => {
  console.log(`[mcp] listening on http://127.0.0.1:${PORT}`);
});
