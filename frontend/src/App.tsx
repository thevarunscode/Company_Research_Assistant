import { useEffect, useRef, useState } from 'react'
import ChatInput from './components/ChatInput'
import Hero from './components/Hero'
import ProgressCard from './components/ProgressCard'
import ReportCard from './components/ReportCard'
import Sidebar from './components/Sidebar'
import {
  DEFAULT_MODEL,
  streamResearch,
  type Report,
  type ResearchConfig,
} from './lib/api'
import type { ProgressStep } from './components/ProgressCard'

type RunItem = { kind: 'run'; steps: ProgressStep[]; report?: Report; error?: string; done: boolean }
type ChatItem = { kind: 'user'; text: string } | RunItem

const CONFIG_KEY = 'research-ai-config'

function loadConfig(): ResearchConfig {
  try {
    const raw = localStorage.getItem(CONFIG_KEY)
    if (raw) return { model: DEFAULT_MODEL, ...JSON.parse(raw) }
  } catch {
    /* corrupted config — fall through to defaults */
  }
  return { openrouterKey: '', serperKey: '', model: DEFAULT_MODEL }
}

export default function App() {
  const [config, setConfig] = useState<ResearchConfig>(loadConfig)
  const [items, setItems] = useState<ChatItem[]>([])
  const [running, setRunning] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [items])

  const saveConfig = (next: ResearchConfig) => {
    setConfig(next)
    localStorage.setItem(CONFIG_KEY, JSON.stringify(next))
  }

  const updateLastRun = (updater: (run: RunItem) => RunItem) => {
    setItems((prev) => {
      const next = [...prev]
      for (let i = next.length - 1; i >= 0; i--) {
        const item = next[i]
        if (item.kind === 'run') {
          next[i] = updater(item)
          break
        }
      }
      return next
    })
  }

  const research = async (query: string) => {
    if (running) return
    setRunning(true)
    setItems((prev) => [
      ...prev,
      { kind: 'user', text: query },
      { kind: 'run', steps: [], done: false },
    ])

    try {
      await streamResearch(query, config, (event) => {
        if (event.type === 'status') {
          updateLastRun((run) => ({
            ...run,
            steps: [...run.steps, { step: event.step, detail: event.detail }],
          }))
        } else if (event.type === 'result') {
          updateLastRun((run) => ({ ...run, report: event.report, done: true }))
        } else {
          updateLastRun((run) => ({ ...run, error: event.message, done: true }))
        }
      })
    } catch (err) {
      updateLastRun((run) => ({
        ...run,
        error: err instanceof Error ? err.message : 'Something went wrong.',
        done: true,
      }))
    } finally {
      setRunning(false)
      updateLastRun((run) => ({ ...run, done: true }))
    }
  }

  return (
    <div className="grain flex h-full overflow-hidden">
      <Sidebar
        config={config}
        onSave={saveConfig}
        onNewResearch={() => setItems([])}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <header className="flex items-center gap-3 border-b border-ink-800 bg-ink-950/90 px-5 py-3.5">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-ink-300 hover:text-ink-100 md:hidden"
            aria-label="Open sidebar"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6">
              <path d="M2 4.5h14M2 9h14M2 13.5h14" strokeLinecap="round" />
            </svg>
          </button>
          <span className="text-sm font-semibold tracking-tight">Company Research</span>
          <span className="micro flex items-center gap-1.5 rounded-full border border-mint-400/25 bg-mint-400/10 px-2.5 py-1 text-mint-400">
            <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mint-400" />
            Live
          </span>
        </header>

        {/* Conversation */}
        <div ref={scrollRef} className="hero-glow flex-1 overflow-y-auto">
          {items.length === 0 ? (
            <Hero onExample={research} />
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6">
              {items.map((item, i) =>
                item.kind === 'user' ? (
                  <div key={i} className="rise self-end">
                    <div className="rounded-xl rounded-br-sm border border-ink-700 bg-ink-800 px-4 py-2.5 text-sm text-ink-100">
                      {item.text}
                    </div>
                  </div>
                ) : (
                  <div key={i} className="flex w-full flex-col gap-4 self-start">
                    {(item.steps.length > 0 || !item.done) && (
                      <ProgressCard steps={item.steps} running={!item.done} />
                    )}
                    {item.report && <ReportCard report={item.report} />}
                    {item.error && (
                      <div className="rise max-w-lg rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                        {item.error}
                      </div>
                    )}
                  </div>
                ),
              )}
            </div>
          )}
        </div>

        <ChatInput disabled={running} onSubmit={research} />
      </main>
    </div>
  )
}
