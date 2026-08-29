import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { StudentsPage } from './pages/StudentsPage'
import { BatchesPage } from './pages/BatchesPage'
import { AttendancePage } from './pages/AttendancePage'
import { FeesPage } from './pages/FeesPage'
import { ExamsPage } from './pages/ExamsPage'
import { MyResultsPage } from './pages/MyResultsPage'
import { NotificationsPage } from './pages/NotificationsPage'

export function defaultRouteForRole(role?: string) {
  if (role === 'admin' || role === 'teacher') return '/dashboard'
  if (role === 'student') return '/my-results'
  return '/notifications'
}

function HomeRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={defaultRouteForRole(user.role)} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <RequireAuth roles={['admin', 'teacher']}>
                  <DashboardPage />
                </RequireAuth>
              }
            />
            <Route
              path="/students"
              element={
                <RequireAuth>
                  <StudentsPage />
                </RequireAuth>
              }
            />
            <Route
              path="/batches"
              element={
                <RequireAuth>
                  <BatchesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/attendance"
              element={
                <RequireAuth roles={['admin', 'teacher']}>
                  <AttendancePage />
                </RequireAuth>
              }
            />
            <Route
              path="/fees"
              element={
                <RequireAuth>
                  <FeesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/exams"
              element={
                <RequireAuth roles={['admin', 'teacher']}>
                  <ExamsPage />
                </RequireAuth>
              }
            />
            <Route
              path="/my-results"
              element={
                <RequireAuth roles={['student']}>
                  <MyResultsPage />
                </RequireAuth>
              }
            />
            <Route
              path="/notifications"
              element={
                <RequireAuth>
                  <NotificationsPage />
                </RequireAuth>
              }
            />
            <Route path="/" element={<HomeRedirect />} />
            <Route path="*" element={<HomeRedirect />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  )
}
