import { useCallback, useEffect, useState } from 'react'
import { CanvasRenderer } from './canvas'
import { loadManifest, writeManifest, hasPuter, type LoadResult } from './puter'
import { SAMPLE_MANIFEST } from './sample-manifest'

const SOURCE_LABEL: Record<LoadResult['source'], string> = {
  'puter-fs': 'Puter filesystem',
  'puter-kv': 'Puter KV',
  mock: 'bundled sample',
}

export default function App() {
  const [result, setResult] = useState<LoadResult | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    const r = await loadManifest()
    setResult(r)
    setLoading(false)
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const seedSample = useCallback(async () => {
    const ok = await writeManifest(SAMPLE_MANIFEST)
    if (ok) await refresh()
  }, [refresh])

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-10 border-b border-surface-border bg-surface-base/90 backdrop-blur px-6 py-3">
        <div className="mx-auto flex max-w-5xl items-center gap-3">
          <span className="text-[15px] font-semibold text-text-heading">Orcha CanvasKit</span>
          <span className="rounded-full border border-surface-borderLight px-2 py-0.5 text-[10px] uppercase tracking-widest text-text-disabled">
            on Puter
          </span>
          <div className="ml-auto flex items-center gap-2">
            {result && (
              <span className="text-[11px] text-text-secondary">
                source: <span className="text-text-body">{SOURCE_LABEL[result.source]}</span>
              </span>
            )}
            {hasPuter() && (
              <button
                type="button"
                onClick={seedSample}
                className="rounded-md border border-surface-border bg-surface-overlay px-3 py-1 text-[12px] text-text-body hover:bg-surface-elevated transition-colors"
              >
                Save sample to Puter
              </button>
            )}
            <button
              type="button"
              onClick={refresh}
              className="rounded-md border border-brand-primary/40 bg-brand-primary/10 px-3 py-1 text-[12px] text-brand-primary hover:bg-brand-primary/20 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-6">
        {loading && !result ? (
          <p className="text-[13px] text-text-secondary">Loading dashboard…</p>
        ) : result ? (
          <>
            <CanvasRenderer manifest={result.manifest} />
            <p className="mt-6 text-[11px] text-text-disabled">{result.detail}</p>
          </>
        ) : null}
      </main>
    </div>
  )
}
