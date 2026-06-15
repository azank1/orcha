export function StreamingDots() {
  return (
    <div className="flex items-center gap-2 px-1">
      <div className="flex items-center gap-1.5">
        <span className="size-[7px] rounded-full bg-brand-primary opacity-40 animate-pulse-dot" aria-hidden="true" />
        <span className="size-[7px] rounded-full bg-brand-primary opacity-60 animate-pulse-dot" aria-hidden="true" />
        <span className="size-[7px] rounded-full bg-brand-primary opacity-80 animate-pulse-dot" aria-hidden="true" />
      </div>
      <span className="text-label text-text-disabled">SuperAgent is thinking…</span>
    </div>
  )
}
