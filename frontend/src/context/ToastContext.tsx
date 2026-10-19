import { createContext, useCallback, useContext, useMemo, useState } from 'react'

type Tone = 'info' | 'success' | 'warning' | 'error'

interface Toast {
  id: number
  message: string
  tone: Tone
}

interface ToastApi {
  push: (message: string, tone?: Tone) => void
}

const ToastContext = createContext<ToastApi | null>(null)

const tones: Record<Tone, string> = {
  info: 'border-sky-500/40 bg-slate-900 text-sky-100',
  success: 'border-emerald-500/40 bg-slate-900 text-emerald-100',
  warning: 'border-amber-500/50 bg-slate-900 text-amber-100',
  error: 'border-red-500/50 bg-slate-900 text-red-100',
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const push = useCallback((message: string, tone: Tone = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((current) => [...current.slice(-3), { id, message, tone }])
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id))
    }, 8000)
  }, [])

  const value = useMemo(() => ({ push }), [push])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
        {toasts.map((toast) => (
          <div key={toast.id} className={`pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-lg ${tones[toast.tone]}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('ToastProvider is missing')
  return context
}
