import { useCallback, useEffect, useState } from 'react'
import { apiGet } from '../services/api'

export function usePolling<T>(url: string | null, intervalMs = 2500) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    if (!url) return
    try {
      const result = await apiGet<T>(url)
      setData(result)
      setError(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => {
    setLoading(true)
    void reload()
    const timer = window.setInterval(() => void reload(), intervalMs)
    return () => window.clearInterval(timer)
  }, [reload, intervalMs])

  return { data, error, loading, reload }
}
