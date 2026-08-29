import { useEffect, useState, type FormEvent } from 'react'
import { api, apiErrorMessage, type Paginated } from '../api/client'
import type { Batch, FeeStructure, OutstandingReport, Payment } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { Button, Card, ErrorBanner, Input, Loading, PageTitle, Select, SuccessBanner, Table } from '../components/ui'
import { loadRazorpayCheckout } from '../razorpay'

export function FeesPage() {
  const { user } = useAuth()
  if (user?.role === 'admin' || user?.role === 'teacher') return <StaffFeesView isAdmin={user.role === 'admin'} />
  return <SelfServiceFeesView />
}

function StaffFeesView({ isAdmin }: { isAdmin: boolean }) {
  const [structures, setStructures] = useState<FeeStructure[]>([])
  const [batches, setBatches] = useState<Batch[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [outstanding, setOutstanding] = useState<OutstandingReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [batch, setBatch] = useState('')
  const [amount, setAmount] = useState('')
  const [dueDate, setDueDate] = useState('')

  const loadAll = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      api.get<Paginated<FeeStructure>>('/fees/structures/', { params: { page_size: 100 } }),
      api.get<Paginated<Batch>>('/batches/', { params: { page_size: 100 } }),
      api.get<Paginated<Payment>>('/fees/payments/', { params: { page_size: 50 } }),
    ])
      .then(([structuresRes, batchesRes, paymentsRes]) => {
        setStructures(structuresRes.data.results)
        setBatches(batchesRes.data.results)
        setPayments(paymentsRes.data.results)
      })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load fees data.')))
      .finally(() => setLoading(false))
  }

  useEffect(loadAll, [])

  const handleCreateStructure = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await api.post('/fees/structures/', { name, batch: Number(batch), amount, due_date: dueDate })
      setName('')
      setBatch('')
      setAmount('')
      setDueDate('')
      setMessage('Fee structure created.')
      loadAll()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create fee structure.'))
    }
  }

  const loadOutstanding = async () => {
    setError(null)
    try {
      const { data } = await api.get<OutstandingReport>('/fees/payments/outstanding/')
      setOutstanding(data)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load outstanding dues.'))
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageTitle>Fees</PageTitle>
      <ErrorBanner message={error} />
      <SuccessBanner message={message} />

      {isAdmin && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Create fee structure</h2>
          <form onSubmit={handleCreateStructure} className="flex flex-wrap items-end gap-2">
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              Name
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
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
              Amount (₹)
              <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              Due date
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required />
            </label>
            <Button type="submit">Add</Button>
          </form>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Fee structures</h2>
        {loading ? (
          <Loading />
        ) : (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Name</th>
                <th className="py-2 pr-2">Batch</th>
                <th className="py-2 pr-2">Amount</th>
                <th className="py-2 pr-2">Due date</th>
              </tr>
            </thead>
            <tbody>
              {structures.map((fs) => (
                <tr key={fs.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{fs.name}</td>
                  <td className="py-2 pr-2">{fs.batch_name}</td>
                  <td className="py-2 pr-2">₹{fs.amount}</td>
                  <td className="py-2 pr-2">{fs.due_date}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Payments</h2>
        <Table>
          <thead>
            <tr className="border-b text-gray-500">
              <th className="py-2 pr-2">Student</th>
              <th className="py-2 pr-2">Fee structure</th>
              <th className="py-2 pr-2">Amount</th>
              <th className="py-2 pr-2">Status</th>
              <th className="py-2 pr-2">Paid at</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id} className="border-b last:border-0">
                <td className="py-2 pr-2">{p.student_name}</td>
                <td className="py-2 pr-2">{p.fee_structure_name}</td>
                <td className="py-2 pr-2">₹{p.amount_paid}</td>
                <td className="py-2 pr-2 capitalize">{p.status}</td>
                <td className="py-2 pr-2">{p.paid_at ?? '—'}</td>
              </tr>
            ))}
            {payments.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-400">
                  No payments yet.
                </td>
              </tr>
            )}
          </tbody>
        </Table>
      </Card>

      {isAdmin && (
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">Outstanding dues</h2>
            <Button onClick={loadOutstanding}>Refresh</Button>
          </div>
          {outstanding && (
            <>
              <p className="mb-2 text-sm text-gray-600">
                Total outstanding: <strong>₹{outstanding.total_outstanding}</strong> across{' '}
                {outstanding.count} due(s)
              </p>
              <Table>
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="py-2 pr-2">Student</th>
                    <th className="py-2 pr-2">Batch</th>
                    <th className="py-2 pr-2">Fee</th>
                    <th className="py-2 pr-2">Amount due</th>
                    <th className="py-2 pr-2">Due date</th>
                  </tr>
                </thead>
                <tbody>
                  {outstanding.outstanding.map((row, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2 pr-2">{row.student_name}</td>
                      <td className="py-2 pr-2">{row.batch_name}</td>
                      <td className="py-2 pr-2">{row.fee_structure_name}</td>
                      <td className="py-2 pr-2">₹{row.amount_due}</td>
                      <td className="py-2 pr-2">{row.due_date}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </>
          )}
        </Card>
      )}
    </div>
  )
}

function SelfServiceFeesView() {
  const [structures, setStructures] = useState<FeeStructure[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [payingId, setPayingId] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    api
      .get<Paginated<FeeStructure>>('/fees/structures/', { params: { page_size: 100 } })
      .then((res) => setStructures(res.data.results))
      .catch((err) => setError(apiErrorMessage(err, 'Could not load fee structures.')))
      .finally(() => setLoading(false))
  }, [])

  const handlePay = async (feeStructureId: number) => {
    setError(null)
    setMessage(null)
    setPayingId(feeStructureId)
    try {
      const { data: order } = await api.post('/fees/payments/initiate/', { fee_structure_id: feeStructureId })
      const Razorpay = await loadRazorpayCheckout()
      const checkout = new Razorpay({
        key: order.razorpay_key_id,
        amount: order.amount,
        currency: order.currency,
        order_id: order.razorpay_order_id,
        name: 'Coaching SaaS',
        description: 'Fee payment',
        handler: async (response: { razorpay_payment_id: string; razorpay_signature: string }) => {
          try {
            await api.post(`/fees/payments/${order.payment_id}/verify/`, {
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            })
            setMessage('Payment verified — thank you!')
          } catch (err) {
            setError(apiErrorMessage(err, 'Payment could not be verified.'))
          }
        },
      })
      checkout.open()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not start payment. Ask your admin if Razorpay is configured.'))
    } finally {
      setPayingId(null)
    }
  }

  return (
    <div>
      <PageTitle>My Fees</PageTitle>
      <ErrorBanner message={error} />
      <SuccessBanner message={message} />
      <Card>
        {loading ? (
          <Loading />
        ) : (
          <Table>
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-2">Fee</th>
                <th className="py-2 pr-2">Batch</th>
                <th className="py-2 pr-2">Amount</th>
                <th className="py-2 pr-2">Due date</th>
                <th className="py-2 pr-2" />
              </tr>
            </thead>
            <tbody>
              {structures.map((fs) => (
                <tr key={fs.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">{fs.name}</td>
                  <td className="py-2 pr-2">{fs.batch_name}</td>
                  <td className="py-2 pr-2">₹{fs.amount}</td>
                  <td className="py-2 pr-2">{fs.due_date}</td>
                  <td className="py-2 pr-2 text-right">
                    <Button onClick={() => handlePay(fs.id)} disabled={payingId === fs.id}>
                      {payingId === fs.id ? 'Starting…' : 'Pay now'}
                    </Button>
                  </td>
                </tr>
              ))}
              {structures.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-400">
                    No fee structures found.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        )}
      </Card>
      <p className="mt-3 text-xs text-gray-400">
        Payment history isn't shown here yet — check with your institute admin, or see the receipt emailed to you
        after paying.
      </p>
    </div>
  )
}
