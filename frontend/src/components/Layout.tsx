import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import type { Role } from '../api/types'

interface NavItem {
  to: string
  label: string
}

function navItemsForRole(role: Role): NavItem[] {
  const isStaff = role === 'admin' || role === 'teacher'
  const items: NavItem[] = []
  if (isStaff) items.push({ to: '/dashboard', label: 'Dashboard' })
  items.push({ to: '/students', label: 'Students' })
  items.push({ to: '/batches', label: 'Batches' })
  if (isStaff) items.push({ to: '/attendance', label: 'Attendance' })
  items.push({ to: '/fees', label: 'Fees' })
  if (isStaff) items.push({ to: '/exams', label: 'Exams' })
  if (role === 'student') items.push({ to: '/my-results', label: 'My Results' })
  items.push({ to: '/notifications', label: 'Notifications' })
  return items
}

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return <>{children}</>

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="text-lg font-semibold text-gray-900">Coaching SaaS</span>
            <nav className="flex gap-4 text-sm">
              {navItemsForRole(user.role).map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `rounded px-2 py-1 ${isActive ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:text-gray-900'}`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm text-gray-600">
            <span>
              {user.first_name || user.username} <span className="text-gray-400">({user.role})</span>
            </span>
            <button
              onClick={handleLogout}
              className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-100"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  )
}
