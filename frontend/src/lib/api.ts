// Same-origin by default; set VITE_API_BASE when the backend lives on another
// host (e.g. Netlify frontend + Render backend).
const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

export interface Competitor {
  name: string
  website: string
}

export interface PricingItem {
  item: string
  price: string
}

export interface Report {
  company_name: string
  website: string
  phone: string
  address: string
  summary: string
  products_services: string[]
  pain_points: string[]
  pricing: PricingItem[]
  competitors: Competitor[]
  sources: string[]
}

export type ResearchEvent =
  | { type: 'status'; step: string; detail: string }
  | { type: 'result'; report: Report }
  | { type: 'error'; message: string }

export interface ResearchConfig {
  openrouterKey: string
  serperKey: string
  model: string
}

export interface ModelOption {
  id: string
  name: string
}

export const FREE_MODELS: ModelOption[] = [
  { id: 'nvidia/nemotron-3-super-120b-a12b:free', name: 'Nemotron 3 Super 120B — Free' },
  { id: 'nvidia/nemotron-3-ultra-550b-a55b:free', name: 'Nemotron 3 Ultra 550B — Free' },
  { id: 'google/gemma-4-31b-it:free', name: 'Gemma 4 31B — Free' },
  { id: 'openai/gpt-oss-20b:free', name: 'GPT-OSS 20B — Free' },
  { id: 'meta-llama/llama-3.3-70b-instruct:free', name: 'Llama 3.3 70B — Free' },
]

export const PREMIUM_MODELS: ModelOption[] = [
  { id: 'anthropic/claude-sonnet-4.5', name: 'Claude Sonnet 4.5' },
  { id: 'anthropic/claude-haiku-4.5', name: 'Claude Haiku 4.5' },
  { id: 'openai/gpt-4o-mini', name: 'GPT-4o mini' },
  { id: 'openai/gpt-4.1', name: 'GPT-4.1' },
  { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
  { id: 'deepseek/deepseek-chat-v3-0324', name: 'DeepSeek V3' },
]

export const CURATED_MODELS: ModelOption[] = [...FREE_MODELS, ...PREMIUM_MODELS]

export const DEFAULT_MODEL = FREE_MODELS[0].id

export async function streamResearch(
  query: string,
  config: ResearchConfig,
  onEvent: (event: ResearchEvent) => void,
): Promise<void> {
  const resp = await fetch(`${API_BASE}/api/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      model: config.model,
      serper_key: config.serperKey || null,
      openrouter_key: config.openrouterKey || null,
    }),
  })
  if (!resp.ok || !resp.body) {
    throw new Error(`Research request failed (${resp.status})`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      const dataLine = chunk.split('\n').find((l) => l.startsWith('data: '))
      if (dataLine) {
        onEvent(JSON.parse(dataLine.slice(6)) as ResearchEvent)
      }
    }
  }
}

export async function downloadPdf(report: Report): Promise<void> {
  const resp = await fetch(`${API_BASE}/api/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(report),
  })
  if (!resp.ok) throw new Error(`PDF generation failed (${resp.status})`)
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  const slug = report.company_name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'company'
  anchor.href = url
  anchor.download = `${slug}-research-report.pdf`
  anchor.click()
  URL.revokeObjectURL(url)
}

export async function fetchModels(): Promise<ModelOption[]> {
  try {
    const resp = await fetch(`${API_BASE}/api/models`)
    if (!resp.ok) return []
    const data = await resp.json()
    return data.models ?? []
  } catch {
    return []
  }
}
