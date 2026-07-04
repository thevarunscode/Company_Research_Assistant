const EXAMPLES = ['stripe.com', 'Tesla', 'Microsoft', 'Figma']

export default function Hero({ onExample }: { onExample: (query: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <div className="micro rise text-gold-400" style={{ animationDelay: '0.05s' }}>
        AI-Powered Intelligence
      </div>
      <h1
        className="rise mt-4 font-display text-5xl leading-[1.05] tracking-tight text-ink-100 md:text-6xl"
        style={{ animationDelay: '0.15s' }}
      >
        Know any company
        <br />
        <em className="text-gold-300">in minutes.</em>
      </h1>
      <p
        className="rise mt-5 max-w-md text-sm leading-relaxed text-ink-300"
        style={{ animationDelay: '0.25s' }}
      >
        Enter a company name or website URL to get AI-powered insights, competitor
        analysis, pain points, and a professional PDF report.
      </p>
      <div className="rise mt-7 flex flex-wrap justify-center gap-2" style={{ animationDelay: '0.35s' }}>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            onClick={() => onExample(example)}
            className="rounded-full border border-ink-700 bg-ink-850 px-4 py-1.5 font-mono text-xs
              text-ink-200 transition-all hover:border-gold-500/50 hover:text-gold-300"
          >
            {example}
          </button>
        ))}
      </div>
      <div className="rise mt-9 flex items-center gap-3 text-ink-500" style={{ animationDelay: '0.45s' }}>
        <span className="h-px w-10 bg-ink-700" />
        <span className="micro">Configure API keys in the sidebar to get started</span>
        <span className="h-px w-10 bg-ink-700" />
      </div>
    </div>
  )
}
