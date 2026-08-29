import { useEffect, useState, type FormEvent } from 'react'
import { api, apiErrorMessage, type Paginated } from '../api/client'
import type { Batch, Exam, ExamReport, Student } from '../api/types'
import { Button, Card, ErrorBanner, Input, Loading, PageTitle, Select, SuccessBanner, Table } from '../components/ui'

export function ExamsPage() {
  const [exams, setExams] = useState<Exam[]>([])
  const [batches, setBatches] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [batch, setBatch] = useState('')
  const [examDate, setExamDate] = useState('')
  const [maxMarks, setMaxMarks] = useState('100')
  const [passingMarks, setPassingMarks] = useState('35')

  const [selectedExam, setSelectedExam] = useState<Exam | null>(null)
  const [examStudents, setExamStudents] = useState<Student[]>([])
  const [marks, setMarks] = useState<Record<number, string>>({})
  const [report, setReport] = useState<ExamReport | null>(null)

  const loadAll = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      api.get<Paginated<Exam>>('/exams/', { params: { page_size: 100 } }),
      api.get<Paginated<Batch>>('/batches/', { params: { page_size: 100 } }),
    ])
      .then(([examsRes, batchesRes]) => {
        setExams(examsRes.data.results)
        setBatches(batchesRes.data.results)
      })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load exams.')))
      .finally(() => setLoading(false))
  }

  useEffect(loadAll, [])

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await api.post('/exams/', {
        title,
        batch: Number(batch),
        exam_date: examDate,
        max_marks: Number(maxMarks),
        passing_marks: Number(passingMarks),
      })
      setTitle('')
      setBatch('')
      setExamDate('')
      setMessage('Exam scheduled.')
      loadAll()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not schedule exam.'))
    }
  }

  const openEnterMarks = async (exam: Exam) => {
    setSelectedExam(exam)
    setReport(null)
    setError(null)
    const { data } = await api.get<Paginated<Student>>('/students/', {
      params: { batch: exam.batch, is_active: true, page_size: 200 },
    })
    setExamStudents(data.results)
    setMarks(Object.fromEntries(data.results.map((s) => [s.id, ''])))
  }

  const handleSaveMarks = async () => {
    if (!selectedExam) return
    setError(null)
    setMessage(null)
    try {
      const entries = examStudents
        .filter((s) => marks[s.id] !== '')
        .map((s) => ({ student_id: s.id, marks_obtained: Number(marks[s.id]) }))
      const { data } = await api.post(`/exams/${selectedExam.id}/enter-marks/`, { entries })
      setMessage(`Marks saved — ${data.created} created, ${data.updated} updated.`)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not save marks.'))
    }
  }

  const loadReport = async (exam: Exam) => {
    setSelectedExam(null)
    setError(null)
    try {
      const { data } = await api.get<ExamReport>(`/exams/${exam.id}/report/`)
      setReport(data)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load report.'))
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageTitle>Exams</PageTitle>
      <ErrorBanner message={error} />
      <SuccessBanner message={message} />

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Schedule an exam</h2>
        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Title
            <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Batch
            <Select value={batch} onChange={(e) => setBatch(e.target.value)} required>
              <option value="">Select a batch</option>
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Exam date
            <Input type="date" value={examDate} onChange={(e) => setExamDate(e.target.value)} required />
          </label>
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Max marks
            <Input type="number" value={maxMarks} onChange={(e) => setMaxMarks(e.target.value)} className="w-20" />
          </label>
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            Passing marks
            <Input
              type="number"
              value={passingMarks}
              onChange={(e) => setPassingMarks(e.target.value)}
              className="w-24"
            />
          </label>
          <Button type="submit">Schedule</Button>
        </form>
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Exams</h2>
        {loading ? (
          <Loading />
        ) : (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Title</th>
                <th className="py-2 pr-2">Batch</th>
                <th className="py-2 pr-2">Date</th>
                <th className="py-2 pr-2">Max marks</th>
                <th className="py-2 pr-2" />
              </tr>
            </thead>
            <tbody>
              {exams.map((exam) => (
                <tr key={exam.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{exam.title}</td>
                  <td className="py-2 pr-2">{exam.batch_name}</td>
                  <td className="py-2 pr-2">{exam.exam_date}</td>
                  <td className="py-2 pr-2">{exam.max_marks}</td>
                  <td className="py-2 pr-2 text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="secondary" onClick={() => openEnterMarks(exam)}>
                        Enter marks
                      </Button>
                      <Button variant="secondary" onClick={() => loadReport(exam)}>
                        Report
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {exams.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-400">
                    No exams scheduled.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        )}
      </Card>

      {selectedExam && (
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">
              Enter marks — {selectedExam.title} (max {selectedExam.max_marks})
            </h2>
            <div className="flex gap-2">
              <Button onClick={handleSaveMarks}>Save marks</Button>
              <Button variant="secondary" onClick={() => setSelectedExam(null)}>
                Close
              </Button>
            </div>
          </div>
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Roll No</th>
                <th className="py-2 pr-2">Name</th>
                <th className="py-2 pr-2">Marks</th>
              </tr>
            </thead>
            <tbody>
              {examStudents.map((s) => (
                <tr key={s.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{s.roll_number}</td>
                  <td className="py-2 pr-2">{s.student_name}</td>
                  <td className="py-2 pr-2">
                    <Input
                      type="number"
                      className="w-24"
                      value={marks[s.id] ?? ''}
                      onChange={(e) => setMarks((prev) => ({ ...prev, [s.id]: e.target.value }))}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {report && (
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-gray-700">
            Report — {report.title} (avg {report.average_percentage}%, {report.pass_count} pass /{' '}
            {report.fail_count} fail)
          </h2>
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Rank</th>
                <th className="py-2 pr-2">Roll No</th>
                <th className="py-2 pr-2">Name</th>
                <th className="py-2 pr-2">Marks</th>
                <th className="py-2 pr-2">%</th>
                <th className="py-2 pr-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {report.results.map((row) => (
                <tr key={row.student_id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{row.rank}</td>
                  <td className="py-2 pr-2">{row.roll_number}</td>
                  <td className="py-2 pr-2">{row.student_name}</td>
                  <td className="py-2 pr-2">{row.marks_obtained}</td>
                  <td className="py-2 pr-2">{row.percentage}%</td>
                  <td className={`py-2 pr-2 ${row.status === 'pass' ? 'text-green-600' : 'text-red-600'}`}>
                    {row.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}
    </div>
  )
}
