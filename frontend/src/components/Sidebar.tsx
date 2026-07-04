import { useEffect, useState } from 'react'
import {
  CURATED_MODELS,
  FREE_MODELS,
  PREMIUM_MODELS,
  fetchModels,
  type ModelOption,
  type ResearchConfig,
} from '../lib/api'

interface SidebarProps {
  config: ResearchConfig
  onSave: (config: ResearchConfig) => void
  onNewResearch: () => void
  open: boolean
  onClose: () => void
}

const STEPS = [
  'Enter a company name or URL',
  'Serper.dev searches and crawls it',
  'OpenRouter AI generates insights',
  'Download a professional PDF report',
]

export default function Sidebar({ config, onSave, onNewResearch, open, onClose }: SidebarProps) {
  const [draft, setDraft] = useState(config)
  const [models, setModels] = useState<ModelOption[]>([])
  const [saved, setSaved] = useState(false)

  useEffect(() => setDraft(config), [config])
  useEffect(() => {
    fetchModels().then(setModels)
  }, [])

  const curatedIds = new Set(CURATED_MODELS.map((m) => m.id))
  const others = models.filter((m) => !curatedIds.has(m.id))

  const save = () => {
    onSave(draft)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-black/60 md:hidden" onClick={onClose} />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-ink-800 bg-ink-900
          transition-transform duration-300 md:static md:translate-x-0
          ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Brand */}
        <div className="flex items-center gap-3 border-b border-ink-800 px-5 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold-400 font-display text-lg text-ink-950">
            R
          </div>
          <div>
            <div className="text-sm font-semibold tracking-tight">Research AI</div>
            <div className="micro text-ink-500">Company Intelligence</div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <button
            onClick={() => {
              onNewResearch()
              onClose()
            }}
            className="mb-5 w-full rounded-lg border border-ink-700 bg-ink-850 px-4 py-2.5 text-sm text-ink-200
              transition-colors hover:border-gold-500/40 hover:text-ink-100"
          >
            <span className="mr-1.5 text-gold-400">+</span> New Research
          </button>

          <div className="micro mb-2 text-ink-500">OpenRouter API Key</div>
          <input
            type="password"
            value={draft.openrouterKey}
            onChange={(e) => setDraft({ ...draft, openrouterKey: e.target.value })}
            placeholder="YOUR_OPENROUTER_API_KEY"
            className="mb-4 w-full rounded-lg border border-ink-700 bg-ink-850 px-3 py-2 font-mono text-xs
              text-ink-100 placeholder:text-ink-500 focus:border-gold-500/60 focus:outline-none"
          />

          <div className="micro mb-2 text-ink-500">Serper.dev API Key</div>
          <input
            type="password"
            value={draft.serperKey}
            onChange={(e) => setDraft({ ...draft, serperKey: e.target.value })}
            placeholder="Your Serper key…"
            className="mb-4 w-full rounded-lg border border-ink-700 bg-ink-850 px-3 py-2 font-mono text-xs
              text-ink-100 placeholder:text-ink-500 focus:border-gold-500/60 focus:outline-none"
          />

          <div className="micro mb-2 text-ink-500">AI Model</div>
          <select
            value={draft.model}
            onChange={(e) => setDraft({ ...draft, model: e.target.value })}
            className="mb-5 w-full appearance-none rounded-lg border border-ink-700 bg-ink-850 px-3 py-2
              text-xs text-ink-100 focus:border-gold-500/60 focus:outline-none"
          >
            <optgroup label="Free — no credits needed">
              {FREE_MODELS.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </optgroup>
            <optgroup label="Premium — needs OpenRouter credits">
              {PREMIUM_MODELS.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </optgroup>
            {others.length > 0 && (
              <optgroup label={`All OpenRouter models (${others.length})`}>
                {others.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </optgroup>
            )}
          </select>

          <button
            onClick={save}
            className={`w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-all
              ${saved
                ? 'bg-mint-400/15 text-mint-400'
                : 'bg-gold-400 text-ink-950 hover:bg-gold-300'}`}
          >
            {saved ? 'Saved ✓' : 'Save Configuration'}
          </button>

          <div className="mt-7 border-t border-ink-800 pt-5">
            <div className="micro mb-3 text-ink-500">How it works</div>
            <ol className="space-y-2.5">
              {STEPS.map((step, i) => (
                <li key={step} className="flex items-start gap-2.5 text-xs text-ink-300">
                  <span className="mt-px flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded
                    bg-ink-800 font-mono text-[10px] text-gold-400">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </div>

        <div className="micro border-t border-ink-800 px-5 py-3 text-ink-500">
          openrouter · serper · reportlab
        </div>
      </aside>
    </>
  )
}
