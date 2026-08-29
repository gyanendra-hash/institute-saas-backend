import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api, apiErrorMessage, type Paginated } from '../api/client'
import type { Batch, Student } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { Button, Card, ErrorBanner, Input, Loading, PageTitle, Select, SuccessBanner, Table } from '../components/ui'

export function StudentsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [students, setStudents] = useState<Student[]>([])
  const [batches, setBatches] = useState<Batch[]>([])
  const [search, setSearch] = useState('')
  const [batchFilter, setBatchFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [newUserId, setNewUserId] = useState('')
  const [newBatch, setNewBatch] = useState('')
  const [newGuardianName, setNewGuardianName] = useState('')
  const [newGuardianPhone, setNewGuardianPhone] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadBatches = () => {
    api.get<Paginated<Batch>>('/batches/', { params: { page_size: 100 } }).then((res) => setBatches(res.data.results))
  }

  const loadStudents = () => {
    setLoading(true)
    setError(null)
    api
      .get<Paginated<Student>>('/students/', {
        params: { search: search || undefined, batch: batchFilter || undefined, page_size: 50 },
      })
      .then((res) => setStudents(res.data.results))
      .catch((err) => setError(apiErrorMessage(err, 'Could not load students.')))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadBatches()
  }, [])

  useEffect(() => {
    const timeout = setTimeout(loadStudents, 300)
    return () => clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, batchFilter])

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await api.post('/students/', {
        user: Number(newUserId),
        batch: newBatch ? Number(newBatch) : null,
        guardian_name: newGuardianName,
        guardian_phone: newGuardianPhone,
      })
      setNewUserId('')
      setNewBatch('')
      setNewGuardianName('')
      setNewGuardianPhone('')
      setMessage('Student created.')
      loadStudents()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create student.'))
    }
  }

  const handleDeactivate = async (id: number) => {
    try {
      await api.post(`/students/${id}/deactivate/`)
      loadStudents()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not deactivate student.'))
    }
  }

  const handleBulkImport = async () => {
    const file = fileInputRef.current?.files?.[0]
    if (!file) return
    setError(null)
    setMessage(null)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const { data } = await api.post('/students/bulk-import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setMessage(`Imported ${data.created} student(s).`)
      if (fileInputRef.current) fileInputRef.current.value = ''
      loadStudents()
    } catch (err) {
      setError(apiErrorMessage(err, 'Bulk import failed.'))
    }
  }

  return (
    <div>
      <PageTitle>Students</PageTitle>
      <ErrorBanner message={error} />
      <SuccessBanner message={message} />

      <div className="mb-4 flex flex-wrap gap-2">
        <Input placeholder="Search by name or roll no." value={search} onChange={(e) => setSearch(e.target.value)} />
        <Select value={batchFilter} onChange={(e) => setBatchFilter(e.target.value)}>
          <option value="">All batches</option>
          {batches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </Select>
      </div>

      {isAdmin && (
        <Card className="mb-4">
          <div className="mb-3 flex flex-wrap items-end gap-4">
            <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-2">
              <label className="flex flex-col gap-1 text-xs text-gray-500">
                User ID
                <Input
                  className="w-24"
                  value={newUserId}
                  onChange={(e) => setNewUserId(e.target.value)}
                  required
                  title="Existing user account id — create the login via Django admin first."
                />
              </label>
              <label className="flex flex-col gap-1 text-xs text-gray-500">
                Batch
                <Select value={newBatch} onChange={(e) => setNewBatch(e.target.value)}>
                  <option value="">Unassigned</option>
                  {batches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </Select>
              </label>
              <label className="flex flex-col gap-1 text-xs text-gray-500">
                Guardian name
                <Input value={newGuardianName} onChange={(e) => setNewGuardianName(e.target.value)} />
              </label>
              <label className="flex flex-col gap-1 text-xs text-gray-500">
                Guardian phone
                <Input value={newGuardianPhone} onChange={(e) => setNewGuardianPhone(e.target.value)} />
              </label>
              <Button type="submit">Add student</Button>
            </form>
          </div>
          <p className="mb-3 text-xs text-gray-400">
            The user login must already exist (created via Django admin) — roll number is auto-generated.
          </p>
          <div className="flex items-center gap-2 border-t pt-3">
            <input ref={fileInputRef} type="file" accept=".csv" className="text-xs" />
            <Button type="button" variant="secondary" onClick={handleBulkImport}>
              Bulk import CSV
            </Button>
            <span className="text-xs text-gray-400">
              Columns: username, first_name, last_name, email, batch, roll_number, guardian_name, guardian_phone
            </span>
          </div>
        </Card>
      )}

      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Roll No</th>
                <th className="py-2 pr-2">Name</th>
                <th className="py-2 pr-2">Batch</th>
                <th className="py-2 pr-2">Guardian phone</th>
                <th className="py-2 pr-2">Status</th>
                {isAdmin && <th className="py-2 pr-2" />}
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{s.roll_number}</td>
                  <td className="py-2 pr-2">{s.student_name}</td>
                  <td className="py-2 pr-2">{s.batch_name ?? '—'}</td>
                  <td className="py-2 pr-2">{s.guardian_phone || '—'}</td>
                  <td className="py-2 pr-2">
                    {s.is_active ? (
                      <span className="text-green-600">Active</span>
                    ) : (
                      <span className="text-gray-400">Inactive</span>
                    )}
                  </td>
                  {isAdmin && (
                    <td className="py-2 pr-2 text-right">
                      {s.is_active && (
                        <Button variant="danger" onClick={() => handleDeactivate(s.id)}>
                          Deactivate
                        </Button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              {students.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-gray-400">
                    No students found.
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
