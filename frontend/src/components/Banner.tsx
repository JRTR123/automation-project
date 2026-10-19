const tones = {
  error: 'border-red-500/40 bg-red-500/10 text-red-100',
  info: 'border-sky-500/40 bg-sky-500/10 text-sky-100',
  warning: 'border-amber-500/40 bg-amber-500/10 text-amber-100',
  success: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-100',
}

export function Banner({
  tone,
  children,
}: {
  tone: keyof typeof tones
  children: React.ReactNode
}) {
  return <div className={`rounded-lg border px-4 py-3 text-sm ${tones[tone]}`}>{children}</div>
}

export function buttonClass(tone: 'primary' | 'danger' | 'ghost' = 'ghost') {
  const base = 'rounded-md px-3 py-1.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40'
  if (tone === 'primary') return `${base} bg-sky-500 text-slate-950 hover:bg-sky-400`
  if (tone === 'danger') return `${base} bg-red-600 text-white hover:bg-red-500`
  return `${base} bg-slate-800 text-slate-100 ring-1 ring-slate-700 hover:bg-slate-700`
}
