export function KpiCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </article>
  )
}

export function OeeBar({ value }: { value: number }) {
  const percent = Math.max(0, Math.min(100, value * 100))
  const color = percent >= 85 ? 'bg-emerald-400' : percent >= 60 ? 'bg-amber-400' : 'bg-red-400'
  return (
    <div className="h-2 rounded-full bg-slate-800">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${percent}%` }} />
    </div>
  )
}
