import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { apiErrorMessage, api } from '../api/client'
import { Button, Card, ErrorBanner, Input } from '../components/ui'
import { defaultRouteForRole } from '../App'
import type { User } from '../api/types'

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) {
    return <Navigate to={defaultRouteForRole(user.role)} replace />
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(username, password)
      const { data: me } = await api.get<User>('/auth/me/')
      navigate(defaultRouteForRole(me.role))
    } catch (err) {
      setError(apiErrorMessage(err, 'Invalid username or password.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 text-xl font-semibold text-gray-900">Coaching SaaS</h1>
        <p className="mb-4 text-sm text-gray-500">Sign in to your institute workspace.</p>
        <ErrorBanner message={error} />
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-sm text-gray-700">
            Username
            <Input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          </label>
          <label className="flex flex-col gap-1 text-sm text-gray-700">
            Password
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <Button type="submit" disabled={submitting} className="mt-2 w-full">
            {submitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
