import { useEffect, useState } from 'react'
import { api, apiErrorMessage, type Paginated } from '../api/client'
import type { AttendanceStatus, Batch, BatchAttendanceReport, Student, StudentAttendanceReport } from '../api/types'
import { Button, Card, ErrorBanner, Input, PageTitle, Select, SuccessBanner, Table } from '../components/ui'

const STATUS_OPTIONS: AttendanceStatus[] = ['present', 'absent', 'leave']

export function AttendancePage() {
  const [batches, setBatches] = useState<Batch[]>([])
  const [markBatchId, setMarkBatchId] = useState('')
  const [markDate, setMarkDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [markStudents, setMarkStudents] = useState<Student[]>([])
  const [statuses, setStatuses] = useState<Record<number, AttendanceStatus>>({})
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [reportBatchId, setReportBatchId] = useState('')
  const [batchReport, setBatchReport] = useState<BatchAttendanceReport | null>(null)
  const [studentReport, setStudentReport] = useState<StudentAttendanceReport | null>(null)
  const [reportStudentId, setReportStudentId] = useState('')

  useEffect(() => {
    api.get<Paginated<Batch>>('/batches/', { params: { page_size: 100 } }).then((res) => setBatches(res.data.results))
  }, [])

  useEffect(() => {
    if (!markBatchId) {
      setMarkStudents([])
      return
    }
    api
      .get<Paginated<Student>>('/students/', { params: { batch: markBatchId, is_active: true, page_size: 200 } })
      .then((res) => {
        setMarkStudents(res.data.results)
        setStatuses(Object.fromEntries(res.data.results.map((s) => [s.id, 'present' as AttendanceStatus])))
      })
  }, [markBatchId])

  const handleBulkMark = async () => {
    setError(null)
    setMessage(null)
    try {
      const { data } = await api.post('/attendance/bulk-mark/', {
        batch_id: Number(markBatchId),
        date: markDate,
        entries: markStudents.map((s) => ({ student_id: s.id, status: statuses[s.id] })),
      })
      setMessage(`Attendance saved — ${data.created} created, ${data.updated} updated.`)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not save attendance.'))
    }
  }

  const loadBatchReport = async () => {
    if (!reportBatchId) return
    setError(null)
    setStudentReport(null)
    try {
      const { data } = await api.get<BatchAttendanceReport>('/attendance/report/', {
        params: { batch_id: reportBatchId },
      })
      setBatchReport(data)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load report.'))
    }
  }

  const loadStudentReport = async () => {
    if (!reportStudentId) return
    setError(null)
    setBatchReport(null)
    try {
      const { data } = await api.get<StudentAttendanceReport>('/attendance/report/', {
        params: { student_id: reportStudentId },
      })
      setStudentReport(data)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load report.'))
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageTitle>Attendance</PageTitle>
      <ErrorBanner message={error} />
      <SuccessBanner message={message} />

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Mark attendance for a batch</h2>
        <div className="mb-3 flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Batch
            <Select value={markBatchId} onChange={(e) => setMarkBatchId(e.target.value)}>
              <option value="">Select a batch</option>
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Date
            <Input type="date" value={markDate} onChange={(e) => setMarkDate(e.target.value)} />
          </label>
          <Button onClick={handleBulkMark} disabled={markStudents.length === 0}>
            Save attendance
          </Button>
        </div>
        {markStudents.length > 0 && (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Roll No</th>
                <th className="py-2 pr-2">Name</th>
                <th className="py-2 pr-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {markStudents.map((s) => (
                <tr key={s.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{s.roll_number}</td>
                  <td className="py-2 pr-2">{s.student_name}</td>
                  <td className="py-2 pr-2">
                    <Select
                      value={statuses[s.id]}
                      onChange={(e) => setStatuses((prev) => ({ ...prev, [s.id]: e.target.value as AttendanceStatus }))}
                    >
                      {STATUS_OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </Select>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Batch attendance report</h2>
        <div className="mb-3 flex items-end gap-2">
          <Select value={reportBatchId} onChange={(e) => setReportBatchId(e.target.value)}>
            <option value="">Select a batch</option>
            {batches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </Select>
          <Button onClick={loadBatchReport}>View report</Button>
        </div>
        {batchReport && (
          <>
            <p className="mb-2 text-sm text-gray-600">
              Batch average: <strong>{batchReport.batch_average_percentage}%</strong>
            </p>
            <Table>
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="py-2 pr-2">Roll No</th>
                  <th className="py-2 pr-2">Present</th>
                  <th className="py-2 pr-2">Total</th>
                  <th className="py-2 pr-2">%</th>
                </tr>
              </thead>
              <tbody>
                {batchReport.students.map((row) => (
                  <tr key={row.student_id} className="border-b last:border-0">
                    <td className="py-2 pr-2">{row.roll_number}</td>
                    <td className="py-2 pr-2">{row.present}</td>
                    <td className="py-2 pr-2">{row.total}</td>
                    <td className="py-2 pr-2">{row.attendance_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        )}
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Single student attendance report</h2>
        <div className="mb-3 flex items-end gap-2">
          <Input
            placeholder="Student ID"
            value={reportStudentId}
            onChange={(e) => setReportStudentId(e.target.value)}
            className="w-32"
          />
          <Button onClick={loadStudentReport}>View report</Button>
        </div>
        {studentReport && (
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              Present: <strong>{studentReport.present}</strong>
            </div>
            <div>
              Absent: <strong>{studentReport.absent}</strong>
            </div>
            <div>
              Leave: <strong>{studentReport.leave}</strong>
            </div>
            <div>
              Attendance %: <strong>{studentReport.attendance_percentage}%</strong>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
