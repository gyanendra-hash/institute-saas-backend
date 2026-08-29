import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { Role } from '../api/types'

export function RequireAuth({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading…</div>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (roles && !roles.includes(user.role)) {
    return (
      <div className="p-8 text-center text-red-600">
        You don't have permission to view this page.
      </div>
    )
  }
  return <>{children}</>
}
