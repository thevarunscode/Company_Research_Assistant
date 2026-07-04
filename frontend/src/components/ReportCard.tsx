import { useState } from 'react'
import { downloadPdf, type Report } from '../lib/api'

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-ink-800 bg-ink-850 px-4 py-3">
      <div className="micro mb-1 text-ink-500">{label}</div>
      <div className="text-sm text-ink-100">{value || 'Not publicly listed'}</div>
    </div>
  )
}

export default function ReportCard({ report }: { report: Report }) {
  const [downloading, setDownloading] = useState(false)
  const [pdfError, setPdfError] = useState('')

  const handleDownload = async () => {
    setDownloading(true)
    setPdfError('')
    try {
      await downloadPdf(report)
    } catch {
      setPdfError('PDF generation failed — try again.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="rise w-full max-w-3xl rounded-xl border border-ink-800 bg-ink-900 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-3xl tracking-tight text-ink-100">
            {report.company_name}
          </h2>
          {report.website && (
            <a
              href={report.website}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-block font-mono text-xs text-gold-400 hover:text-gold-300"
            >
              {report.website}
            </a>
          )}
        </div>
        <span className="micro rounded-full border border-mint-400/30 bg-mint-400/10 px-3 py-1.5 text-mint-400">
          Research Complete
        </span>
      </div>

      {/* Contact tiles */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <Tile label="Phone" value={report.phone} />
        <Tile label="Address" value={report.address} />
      </div>

      {/* Summary */}
      {report.summary && (
        <section className="mt-6">
          <div className="micro mb-2.5 text-gold-400">Summary</div>
          <p className="text-sm leading-relaxed text-ink-200">{report.summary}</p>
        </section>
      )}

      {/* Products & services */}
      {report.products_services.length > 0 && (
        <section className="mt-6">
          <div className="micro mb-2.5 text-gold-400">Products &amp; Services</div>
          <div className="flex flex-wrap gap-2">
            {report.products_services.map((item) => (
              <span
                key={item}
                className="rounded-md border border-ink-700 bg-ink-850 px-3 py-1.5 font-mono text-xs text-ink-200"
              >
                {item}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Pain points */}
      {report.pain_points.length > 0 && (
        <section className="mt-6">
          <div className="micro mb-2.5 text-gold-400">AI-Generated Pain Points</div>
          <ul className="space-y-2.5">
            {report.pain_points.map((point) => (
              <li key={point} className="flex gap-2.5 text-sm leading-relaxed text-ink-200">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold-400" />
                {point}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Pricing — rendered only when real prices were found */}
      {report.pricing?.length > 0 && (
        <section className="mt-6">
          <div className="micro mb-2.5 text-gold-400">Pricing</div>
          <div className="overflow-hidden rounded-lg border border-ink-800">
            {report.pricing.map((entry, i) => (
              <div
                key={entry.item}
                className={`flex items-baseline justify-between gap-4 bg-ink-850 px-4 py-2.5
                  ${i > 0 ? 'border-t border-ink-800' : ''}`}
              >
                <span className="text-sm text-ink-100">{entry.item}</span>
                <span className="shrink-0 font-mono text-xs text-gold-300">{entry.price}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Competitors */}
      {report.competitors.length > 0 && (
        <section className="mt-6">
          <div className="micro mb-2.5 text-gold-400">Competitors</div>
          <div className="grid gap-2.5 sm:grid-cols-2">
            {report.competitors.map((competitor) => (
              <a
                key={competitor.name}
                href={competitor.website || undefined}
                target="_blank"
                rel="noreferrer"
                className="group rounded-lg border border-ink-800 bg-ink-850 px-4 py-3 transition-colors hover:border-gold-500/40"
              >
                <div className="text-sm font-semibold text-ink-100 group-hover:text-gold-300">
                  {competitor.name}
                </div>
                <div className="mt-0.5 truncate font-mono text-[11px] text-ink-300">
                  {competitor.website || '—'}
                </div>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Sources */}
      {report.sources.length > 0 && (
        <details className="mt-6">
          <summary className="micro cursor-pointer text-ink-500 hover:text-ink-300">
            Sources ({report.sources.length} pages analyzed)
          </summary>
          <ul className="mt-2 space-y-1">
            {report.sources.map((source) => (
              <li key={source} className="truncate font-mono text-[11px] text-ink-300">
                {source}
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* Actions */}
      <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-ink-800 pt-5">
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="rounded-lg bg-gold-400 px-5 py-2.5 text-sm font-semibold text-ink-950
            transition-all hover:bg-gold-300 disabled:opacity-60"
        >
          {downloading ? 'Generating…' : '↓ Download PDF Report'}
        </button>
        {pdfError && <span className="text-xs text-red-400">{pdfError}</span>}
      </div>
    </div>
  )
}
