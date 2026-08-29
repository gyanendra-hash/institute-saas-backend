import { useEffect, useState, type FormEvent } from 'react'
import { api, apiErrorMessage, type Paginated } from '../api/client'
import type { Batch } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { Button, Card, ErrorBanner, Input, Loading, PageTitle, SuccessBanner, Table } from '../components/ui'

export function BatchesPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [batches, setBatches] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [course, setCourse] = useState('')
  const [startDate, setStartDate] = useState('')

  const [assignBatchId, setAssignBatchId] = useState<number | null>(null)
  const [studentIds, setStudentIds] = useState('')

  const loadBatches = () => {
    setLoading(true)
    setError(null)
    api
      .get<Paginated<Batch>>('/batches/', { params: { page_size: 100 } })
      .then((res) => setBatches(res.data.results))
      .catch((err) => setError(apiErrorMessage(err, 'Could not load batches.')))
      .finally(() => setLoading(false))
  }

  useEffect(loadBatches, [])

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await api.post('/batches/', { name, course, start_date: startDate })
      setName('')
      setCourse('')
      setStartDate('')
      setMessage('Batch created.')
      loadBatches()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create batch.'))
    }
  }

  const handleAssign = async (event: FormEvent) => {
    event.preventDefault()
    if (!assignBatchId) return
    setError(null)
    setMessage(null)
    const ids = studentIds
      .split(',')
      .map((s) => Number(s.trim()))
      .filter((n) => !Number.isNaN(n))
    try {
      const { data } = await api.post(`/batches/${assignBatchId}/assign_students/`, { student_ids: ids })
      setMessage(`Assigned ${data.assigned} student(s).`)
      setStudentIds('')
      setAssignBatchId(null)
      loadBatches()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not assign students.'))
    }
  }

  return (
    <div>
      <PageTitle>Batches</PageTitle>
      <ErrorBanner message={error} />
      <SuccessBanner message={message} />

      {isAdmin && (
        <Card className="mb-4">
          <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              Name
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              Course
              <Input value={course} onChange={(e) => setCourse(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              Start date
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
            </label>
            <Button type="submit">Add batch</Button>
          </form>

          {assignBatchId && (
            <form onSubmit={handleAssign} className="mt-3 flex flex-wrap items-end gap-2 border-t pt-3">
              <span className="text-xs text-gray-500">
                Assign students to <strong>{batches.find((b) => b.id === assignBatchId)?.name}</strong>
              </span>
              <Input
                placeholder="Student IDs, comma-separated"
                value={studentIds}
                onChange={(e) => setStudentIds(e.target.value)}
                className="w-64"
              />
              <Button type="submit">Assign</Button>
              <Button type="button" variant="secondary" onClick={() => setAssignBatchId(null)}>
                Cancel
              </Button>
            </form>
          )}
        </Card>
      )}

      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Name</th>
                <th className="py-2 pr-2">Course</th>
                <th className="py-2 pr-2">Start date</th>
                <th className="py-2 pr-2">Students</th>
                <th className="py-2 pr-2">Status</th>
                {isAdmin && <th className="py-2 pr-2" />}
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{b.name}</td>
                  <td className="py-2 pr-2">{b.course}</td>
                  <td className="py-2 pr-2">{b.start_date}</td>
                  <td className="py-2 pr-2">{b.student_count}</td>
                  <td className="py-2 pr-2">{b.is_active ? 'Active' : 'Inactive'}</td>
                  {isAdmin && (
                    <td className="py-2 pr-2 text-right">
                      <Button variant="secondary" onClick={() => setAssignBatchId(b.id)}>
                        Assign students
                      </Button>
                    </td>
                  )}
                </tr>
              ))}
              {batches.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-gray-400">
                    No batches found.
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
