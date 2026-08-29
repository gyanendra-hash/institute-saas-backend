import { useEffect, useState } from 'react'
import { api, apiErrorMessage, type Paginated } from '../api/client'
import type { Notification } from '../api/types'
import { Card, ErrorBanner, Loading, PageTitle, Table } from '../components/ui'

const STATUS_COLOR: Record<string, string> = {
  sent: 'text-green-600',
  queued: 'text-amber-600',
  failed: 'text-red-600',
}

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<Paginated<Notification>>('/notifications/', { params: { page_size: 50 } })
      .then((res) => setNotifications(res.data.results))
      .catch((err) => setError(apiErrorMessage(err, 'Could not load notifications.')))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageTitle>Notifications</PageTitle>
      <ErrorBanner message={error} />
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Channel</th>
                <th className="py-2 pr-2">Subject</th>
                <th className="py-2 pr-2">Status</th>
                <th className="py-2 pr-2">Sent at</th>
              </tr>
            </thead>
            <tbody>
              {notifications.map((n) => (
                <tr key={n.id} className="border-b last:border-0">
                  <td className="py-2 pr-2 uppercase">{n.channel}</td>
                  <td className="py-2 pr-2">{n.subject || n.message.slice(0, 60)}</td>
                  <td className={`py-2 pr-2 capitalize ${STATUS_COLOR[n.status] ?? ''}`}>{n.status}</td>
                  <td className="py-2 pr-2">{n.sent_at ?? '—'}</td>
                </tr>
              ))}
              {notifications.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-gray-400">
                    No notifications yet.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  )
}
