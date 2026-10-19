import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatClock, formatTime } from '../utils/format'

interface Point {
  timestamp: string
  temperature: number
  vibration: number
  motor_current: number
}

export function SensorChart({
  title,
  data,
  dataKey,
  color,
  unit,
  warning,
  critical,
}: {
  title: string
  data: Point[]
  dataKey: 'temperature' | 'vibration' | 'motor_current'
  color: string
  unit: string
  warning: number
  critical: number
}) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      {data.length === 0 ? (
        <p className="mt-8 text-sm text-slate-400">No readings yet. Start the simulation to collect sensor history.</p>
      ) : (
        <div className="mt-3 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid stroke="#1e293b" />
              <XAxis dataKey="timestamp" tickFormatter={formatClock} minTickGap={28} stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} width={48} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                labelFormatter={(label) => formatTime(String(label))}
              />
              {warning > 0 && <ReferenceLine y={warning} stroke="#f59e0b" strokeDasharray="4 4" />}
              {critical > 0 && <ReferenceLine y={critical} stroke="#ef4444" strokeDasharray="4 4" />}
              <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} strokeWidth={2} name={`${title} (${unit})`} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      {warning > 0 && critical > 0 && (
        <p className="mt-2 text-xs text-slate-500">
          Amber dashed line: warning {warning} {unit}. Red dashed line: critical {critical} {unit}.
        </p>
      )}
    </section>
  )
}
