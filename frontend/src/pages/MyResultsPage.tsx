import { useEffect, useState } from 'react'
import { api, apiErrorMessage } from '../api/client'
import type { MyResults } from '../api/types'
import { Card, ErrorBanner, Loading, PageTitle, Table } from '../components/ui'

export function MyResultsPage() {
  const [results, setResults] = useState<MyResults | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<MyResults>('/exams/my-results/')
      .then((res) => setResults(res.data))
      .catch((err) => setError(apiErrorMessage(err, 'Could not load your results.')))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageTitle>My Results</PageTitle>
      <ErrorBanner message={error} />
      {loading ? (
        <Loading />
      ) : (
        results && (
          <Card>
            <p className="mb-3 text-sm text-gray-600">
              Average across all exams: <strong>{results.average_percentage}%</strong>
            </p>
            <Table>
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="py-2 pr-2">Exam</th>
                  <th className="py-2 pr-2">Batch</th>
                  <th className="py-2 pr-2">Date</th>
                  <th className="py-2 pr-2">Marks</th>
                  <th className="py-2 pr-2">%</th>
                  <th className="py-2 pr-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {results.results.map((row) => (
                  <tr key={row.exam_id} className="border-b last:border-0">
                    <td className="py-2 pr-2">{row.title}</td>
                    <td className="py-2 pr-2">{row.batch_name}</td>
                    <td className="py-2 pr-2">{row.exam_date}</td>
                    <td className="py-2 pr-2">
                      {row.marks_obtained} / {row.max_marks}
                    </td>
                    <td className="py-2 pr-2">{row.percentage}%</td>
                    <td className={`py-2 pr-2 ${row.status === 'pass' ? 'text-green-600' : 'text-red-600'}`}>
                      {row.status}
                    </td>
                  </tr>
                ))}
                {results.results.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-gray-400">
                      No results yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </Card>
        )
      )}
    </div>
  )
}
