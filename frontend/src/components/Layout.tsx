import { useEffect, useRef } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { usePolling } from '../hooks/usePolling'
import type { Alarm, Health } from '../types'
import { useToast } from '../context/ToastContext'
import { Banner } from './Banner'
import { SimulationControls } from './SimulationControls'

const NAV = [
  { to: '/', label: 'Overview', end: true },
  { to: '/machines', label: 'Machines', end: false },
  { to: '/alarms', label: 'Alarms', end: false },
  { to: '/production', label: 'Production & OEE', end: false },
  { to: '/reports', label: 'Reports', end: false },
  { to: '/settings', label: 'Settings', end: false },
]

function pageTitle(pathname: string) {
  if (pathname.startsWith('/machines/')) return 'Machine detail'
  if (pathname.startsWith('/machines')) return 'Machines'
  if (pathname.startsWith('/alarms')) return 'Alarms'
  if (pathname.startsWith('/production')) return 'Production and OEE'
  if (pathname.startsWith('/reports')) return 'Reports and trends'
  if (pathname.startsWith('/settings')) return 'Settings and controls'
  return 'Factory overview'
}

export function Layout() {
  const location = useLocation()
  const health = usePolling<Health>('/api/health', 2500)
  const alarms = usePolling<Alarm[]>('/api/alarms?acknowledged=false', 2500)
  const { push } = useToast()
  const seen = useRef(new Set<number>())
  const ready = useRef(false)

  useEffect(() => {
    if (!alarms.data) return
    if (!ready.current) {
      alarms.data.forEach((alarm) => seen.current.add(alarm.id))
      ready.current = true
      return
    }
    alarms.data.forEach((alarm) => {
      if (seen.current.has(alarm.id)) return
      seen.current.add(alarm.id)
      const tone = alarm.severity === 'CRITICAL' ? 'error' : alarm.severity === 'WARNING' ? 'warning' : 'info'
      push(`${alarm.severity} on ${alarm.machine_name}: ${alarm.description}`, tone)
    })
  }, [alarms.data, push])

  const state = health.data?.simulation
  const stateLabel = state === 'running' ? 'Simulation running' : state === 'paused' ? 'Simulation paused' : 'Simulation stopped'
  const stateClass =
    state === 'running'
      ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40'
      : state === 'paused'
        ? 'bg-amber-500/15 text-amber-200 ring-amber-500/40'
        : 'bg-slate-700 text-slate-300 ring-slate-600'

  return (
    <div className="flex min-h-screen bg-[#070d18] text-slate-100">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-[#0b1220]">
        <div className="border-b border-slate-800 px-5 py-5">
          <p className="text-xs uppercase tracking-[0.2em] text-sky-400">Mechatronics lab</p>
          <h1 className="mt-1 text-lg font-semibold leading-6 text-white">Machine Monitoring</h1>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 text-sm ${
                  isActive ? 'bg-sky-500/15 text-sky-200' : 'text-slate-300 hover:bg-slate-800'
                }`
              }
            >
              <span>{item.label}</span>
              {item.to === '/alarms' && (alarms.data?.length ?? 0) > 0 && (
                <span className="rounded-full bg-red-500 px-2 py-0.5 text-xs font-semibold text-white">{alarms.data?.length}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <p className="mt-auto px-5 py-4 text-xs leading-5 text-slate-500">
          Software simulation only. This dashboard is not connected to a PLC, SCADA system, or physical machine.
        </p>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-6 py-4">
          <div>
            <h2 className="text-xl font-semibold text-white">{pageTitle(location.pathname)}</h2>
            <p className="text-xs text-slate-400">Simulated factory data for academic demonstration</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${stateClass}`}>{stateLabel}</span>
            {health.data && <span className="text-xs text-slate-400">{health.data.simulation_speed}× speed</span>}
            <SimulationControls state={state} onDone={health.reload} />
          </div>
        </header>
        <main className="flex-1 space-y-4 px-6 py-5">
          {health.error && (
            <Banner tone="error">
              {health.error} The dashboard polls the API every 2.5 seconds.
            </Banner>
          )}
          {state === 'paused' && (
            <Banner tone="warning">
              Simulation is paused. Sensor values and production counters will hold until you resume.
            </Banner>
          )}
          <Outlet />
        </main>
      </div>
    </div>
  )
}
