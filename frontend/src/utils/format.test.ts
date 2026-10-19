import { describe, expect, it } from 'vitest'
import { formatDuration, formatPercent, formatScenario, statusTone } from './format'

describe('formatDuration', () => {
  it('formats hours, minutes, and seconds', () => {
    expect(formatDuration(3661)).toBe('1h 1m 1s')
    expect(formatDuration(90)).toBe('1m 30s')
    expect(formatDuration(0)).toBe('0s')
    expect(formatDuration(-4)).toBe('0s')
  })
})

describe('formatPercent', () => {
  it('renders a fraction as a percentage', () => {
    expect(formatPercent(0.856)).toBe('85.6%')
    expect(formatPercent(Number.NaN)).toBe('0.0%')
  })
})

describe('statusTone', () => {
  it('uses green for running and red for fault', () => {
    expect(statusTone('RUNNING').dot).toBe('bg-emerald-400')
    expect(statusTone('RUNNING').label).toBe('Running')
    expect(statusTone('FAULT').dot).toBe('bg-red-400')
    expect(statusTone('IDLE').dot).toBe('bg-sky-400')
    expect(statusTone('STOPPED').label).toBe('Stopped')
  })
})

describe('formatScenario', () => {
  it('labels known simulation scenarios', () => {
    expect(formatScenario(null)).toBe('None')
    expect(formatScenario('high_temperature')).toBe('High temperature')
    expect(formatScenario('machine_fault')).toBe('Machine fault')
  })
})
