export type Role = 'super_admin' | 'admin' | 'teacher' | 'student' | 'parent'

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: Role
  phone: string
  tenant: number | null
}

export interface Batch {
  id: number
  name: string
  course: string
  start_date: string
  end_date: string | null
  is_active: boolean
  student_count: number
}

export interface Student {
  id: number
  user: number
  student_name: string
  batch: number | null
  batch_name: string | null
  roll_number: string
  guardian_name: string
  guardian_phone: string
  date_of_birth: string | null
  is_active: boolean
}

export type AttendanceStatus = 'present' | 'absent' | 'leave'

export interface AttendanceRecord {
  id: number
  student: number
  student_name: string
  date: string
  status: AttendanceStatus
  marked_by: number | null
}

export interface AttendanceReportRow {
  student_id: number
  roll_number: string
  total: number
  present: number
  attendance_percentage: number
}

export interface BatchAttendanceReport {
  batch_id: number
  students: AttendanceReportRow[]
  batch_average_percentage: number
}

export interface StudentAttendanceReport {
  student_id: number
  total: number
  present: number
  absent: number
  leave: number
  attendance_percentage: number
}

export interface FeeStructure {
  id: number
  batch: number
  batch_name: string
  name: string
  amount: string
  due_date: string
}

export type PaymentStatus = 'pending' | 'success' | 'failed'

export interface Payment {
  id: number
  student: number
  student_name: string
  fee_structure: number
  fee_structure_name: string
  amount_paid: string
  razorpay_order_id: string
  razorpay_payment_id: string
  status: PaymentStatus
  paid_at: string | null
  created_at: string
}

export interface OutstandingRow {
  student_id: number
  roll_number: string
  student_name: string
  fee_structure_id: number
  fee_structure_name: string
  batch_id: number
  batch_name: string
  amount_due: string
  due_date: string
}

export interface OutstandingReport {
  outstanding: OutstandingRow[]
  count: number
  total_outstanding: string
}

export interface Exam {
  id: number
  batch: number
  batch_name: string
  title: string
  exam_date: string
  max_marks: number
  passing_marks: number
}

export interface ExamReportRow {
  student_id: number
  roll_number: string
  student_name: string
  marks_obtained: number
  percentage: number
  rank: number
  status: 'pass' | 'fail'
}

export interface ExamReport {
  exam_id: number
  title: string
  max_marks: number
  passing_marks: number
  average_marks: number
  average_percentage: number
  pass_count: number
  fail_count: number
  results: ExamReportRow[]
}

export interface MyResultRow {
  exam_id: number
  title: string
  exam_date: string
  batch_name: string
  marks_obtained: number
  max_marks: number
  percentage: number
  status: 'pass' | 'fail'
}

export interface MyResults {
  student_id: number
  roll_number: string
  results: MyResultRow[]
  average_percentage: number
}

export type NotificationChannel = 'email' | 'sms' | 'whatsapp'
export type NotificationStatus = 'queued' | 'sent' | 'failed'

export interface Notification {
  id: number
  user: number
  channel: NotificationChannel
  subject: string
  message: string
  status: NotificationStatus
  sent_at: string | null
  created_at: string
}

export interface DashboardSummary {
  active_students: number
  revenue_collected: string
  outstanding_dues: string
  attendance_percentage: number | null
  attendance_window_days: number
}
