import type { ReactNode } from 'react'

export function PageTitle({ children }: { children: ReactNode }) {
  return <h1 className="mb-4 text-2xl font-semibold text-gray-900">{children}</h1>
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-lg border border-gray-200 bg-white p-4 shadow-sm ${className}`}>{children}</div>
}

export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null
  return <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{message}</div>
}

export function SuccessBanner({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div className="mb-4 rounded border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{message}</div>
  )
}

export function Loading() {
  return <div className="py-8 text-center text-gray-500">Loading…</div>
}

export function Button({
  children,
  className = '',
  variant = 'primary',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }) {
  const styles: Record<string, string> = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300',
    secondary: 'border border-gray-300 text-gray-700 hover:bg-gray-100',
    danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300',
  }
  return (
    <button className={`rounded px-3 py-1.5 text-sm font-medium ${styles[variant]} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none ${props.className ?? ''}`}
    />
  )
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none ${props.className ?? ''}`}
    />
  )
}

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">{children}</table>
    </div>
  )
}
