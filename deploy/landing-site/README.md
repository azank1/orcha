# Landing site (orcha-landing)

Vite + React + TS landing page for Orcha, deployed on Cloudflare Pages.

## Develop / build

```bash
nvm use 22            # wrangler 4 requires Node >= 22
npm install
npm run build         # outputs dist/
```

## Deploy

Direct-upload via Wrangler (token in env, never in the repo). Make sure you
also set `CLOUDFLARE_ACCOUNT_ID` in your environment:

```bash
export CLOUDFLARE_API_TOKEN=<pages-edit token>
export CLOUDFLARE_ACCOUNT_ID=<your-account-id>
npm run build
echo '/*  /index.html  200' > dist/_redirects   # SPA fallback (already committed? regenerate if missing)
npx wrangler pages deploy dist --project-name orcha-landing --branch main
```

Notes learned at first deploy:

- `--branch main` is required: without it wrangler infers the local git
  branch and ships a **preview** deployment — custom domains keep serving
  "Deployment Not Found" (404) until a production deployment exists.
- Custom domains are attached via the Pages API
  (`POST /accounts/{id}/pages/projects/orcha-landing/domains`), not by
  wrangler. Same-account zone auto-verifies DNS; cert validation takes a
  few minutes.
- `dist/_redirects` with `/*  /index.html  200` keeps client-side routes
  working on refresh.
- Source of truth for content changes: rebuild from the AI Studio project
  or edit `src/`, then redeploy with the commands above.
