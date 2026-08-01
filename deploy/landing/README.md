# Landing page (one-pager)

Static single-file landing for the OSS launch, deployed on Cloudflare Pages
(free tier) at the apex domain.

- `index.html` is self-contained (fonts from Google Fonts CDN, no build step).
- **Before deploy:** copy the current hero clip to `deploy/landing/demo-hero.gif`
  (re-recorded per `docs/assets/README.md` — the GIF is intentionally not
  tracked here so the page never ships a stale recording).
- Deploy: Cloudflare Pages → direct upload of this directory, or
  `npx wrangler pages deploy deploy/landing --project-name orcha-landing`.
