import { useRef, useState, type KeyboardEvent } from 'react'

interface ChatInputProps {
  disabled: boolean
  onSubmit: (query: string) => void
}

export default function ChatInput({ disabled, onSubmit }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const query = value.trim()
    if (!query || disabled) return
    onSubmit(query)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const autoGrow = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  return (
    <div className="border-t border-ink-800 bg-ink-950/90 px-4 pb-4 pt-3 backdrop-blur">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-xl border border-ink-700 bg-ink-850 p-2
          transition-colors focus-within:border-gold-500/50">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            disabled={disabled}
            onChange={(e) => {
              setValue(e.target.value)
              autoGrow()
            }}
            onKeyDown={handleKeyDown}
            placeholder="Enter a company name (e.g. Stripe) or website URL (e.g. https://stripe.com)…"
            className="max-h-[120px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-ink-100
              placeholder:text-ink-500 focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="shrink-0 rounded-lg bg-gold-400 px-4 py-2 text-sm font-semibold text-ink-950
              transition-all hover:bg-gold-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {disabled ? <span className="spinner inline-block" /> : 'Research →'}
          </button>
        </div>
        <div className="micro mt-2.5 text-center text-ink-500">
          Enter to research · Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}
