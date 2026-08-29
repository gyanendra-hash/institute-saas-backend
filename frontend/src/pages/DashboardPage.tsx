import { useEffect, useState } from 'react'
import { api, apiErrorMessage } from '../api/client'
import type { DashboardSummary } from '../api/types'
import { Card, ErrorBanner, Loading, PageTitle, Select } from '../components/ui'

export function DashboardPage() {
  const [days, setDays] = useState(30)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .get<DashboardSummary>('/dashboard/summary/', { params: { days } })
      .then((res) => setSummary(res.data))
      .catch((err) => setError(apiErrorMessage(err, 'Could not load the dashboard.')))
      .finally(() => setLoading(false))
  }, [days])

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <PageTitle>Dashboard</PageTitle>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          Attendance window
          <Select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </Select>
        </label>
      </div>
      <ErrorBanner message={error} />
      {loading || !summary ? (
        <Loading />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Active students" value={summary.active_students} />
          <StatCard label="Revenue collected" value={`₹${summary.revenue_collected}`} />
          <StatCard label="Outstanding dues" value={`₹${summary.outstanding_dues}`} />
          <StatCard
            label={`Attendance % (${summary.attendance_window_days}d)`}
            value={summary.attendance_percentage === null ? 'N/A' : `${summary.attendance_percentage}%`}
          />
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <div className="text-sm text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-gray-900">{value}</div>
    </Card>
  )
}
