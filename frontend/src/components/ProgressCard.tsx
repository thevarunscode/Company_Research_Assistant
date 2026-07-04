export interface ProgressStep {
  step: string
  detail: string
}

const STEP_LABELS: Record<string, string> = {
  resolve: 'Website',
  crawl: 'Crawling',
  enrich: 'Public Sources',
  analyze: 'AI Analysis',
}

interface ProgressCardProps {
  steps: ProgressStep[]
  running: boolean
}

export default function ProgressCard({ steps, running }: ProgressCardProps) {
  return (
    <div className="rise max-w-lg rounded-xl border border-ink-800 bg-ink-900 p-5">
      <div className="micro mb-4 flex items-center gap-2 text-gold-400">
        {running && <span className="spinner" />}
        Researching
      </div>
      <ul className="space-y-2.5">
        {steps.map((s, i) => {
          const isLast = i === steps.length - 1
          const active = running && isLast
          return (
            <li key={i} className="flex items-start gap-2.5 text-xs">
              <span className="mt-0.5 shrink-0">
                {active ? (
                  <span className="spinner" />
                ) : (
                  <span className="flex h-[13px] w-[13px] items-center justify-center rounded-full bg-mint-400/15 text-[9px] text-mint-400">
                    ✓
                  </span>
                )}
              </span>
              <span>
                <span className="mr-2 font-mono text-[10px] uppercase tracking-widest text-ink-500">
                  {STEP_LABELS[s.step] ?? s.step}
                </span>
                <span className={active ? 'shimmer-text' : 'text-ink-200'}>{s.detail}</span>
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
