import type { ChecklistTask } from '../../types'

const STATUS_ICON: Record<string, { icon: string; color: string }> = {
  pending: { icon: '○', color: 'text-text-disabled' },
  running: { icon: '◐', color: 'text-brand-primary-light' },
  done:    { icon: '✓', color: 'text-semantic-success' },
  failed:  { icon: '✕', color: 'text-semantic-error' },
}

interface PlanningStepsProps {
  tasks: ChecklistTask[]
}

/**
 * Inline PnD decomposition steps shown in the main timeline while a run is
 * in progress. Mimics the "Planning & Discovery" phase visually — each task
 * maps to a step in the DAG the planner produced.
 */
export function PlanningSteps({ tasks }: PlanningStepsProps) {
  if (tasks.length === 0) return null

  const allDone = tasks.every((t) => t.status === 'done' || t.status === 'failed')

  return (
    <div className="ml-2 border-l-2 border-brand-primary/30 pl-4 animate-tool-enter">
      <div className="mb-2 flex items-center gap-2">
        {allDone ? (
          <span className="text-[10px] font-semibold uppercase tracking-widest text-semantic-success">
            Plan ready
          </span>
        ) : (
          <>
            <span className="flex items-center gap-0.5" aria-hidden>
              <span className="size-[5px] rounded-full bg-brand-primary opacity-50 animate-pulse-dot" />
              <span className="size-[5px] rounded-full bg-brand-primary opacity-65 animate-pulse-dot" />
              <span className="size-[5px] rounded-full bg-brand-primary opacity-80 animate-pulse-dot" />
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-widest text-brand-primary-light">
              Planning
            </span>
          </>
        )}
      </div>
      <ol className="flex flex-col gap-1.5">
        {tasks.map((task, i) => {
          const s = STATUS_ICON[task.status] ?? STATUS_ICON.pending
          return (
            <li
              key={task.id}
              className="flex items-start gap-2 animate-canvas-enter"
              style={{ animationDelay: `${i * 80}ms`, opacity: 0, animationFillMode: 'forwards' }}
            >
              <span className={`mt-px shrink-0 text-[13px] font-mono ${s.color}`} aria-hidden>
                {s.icon}
              </span>
              <span
                className={`text-[12px] leading-snug transition-colors duration-300 ${
                  task.status === 'done'
                    ? 'text-text-secondary line-through decoration-text-disabled/40'
                    : task.status === 'running'
                      ? 'text-text-body font-medium'
                      : task.status === 'failed'
                        ? 'text-semantic-error'
                        : 'text-text-disabled'
                }`}
              >
                {task.label}
              </span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
