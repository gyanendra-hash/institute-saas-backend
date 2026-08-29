interface RazorpayOptions {
  key: string
  amount: number
  currency: string
  order_id: string
  name: string
  description?: string
  handler: (response: { razorpay_payment_id: string; razorpay_order_id: string; razorpay_signature: string }) => void
}

interface RazorpayInstance {
  open: () => void
}

type RazorpayConstructor = new (options: RazorpayOptions) => RazorpayInstance

declare global {
  interface Window {
    Razorpay?: RazorpayConstructor
  }
}

const CHECKOUT_SRC = 'https://checkout.razorpay.com/v1/checkout.js'

/**
 * Lazily loads Razorpay's Checkout script — only when a student actually
 * clicks "Pay now", not on every page load. Sandbox note: without a real
 * RAZORPAY_KEY_ID configured on the backend, `initiate` still returns a
 * usable order shape (apps/fees/services/payment_gateway.py), so this
 * opens Checkout with whatever key the backend is configured with.
 */
export function loadRazorpayCheckout(): Promise<RazorpayConstructor> {
  if (window.Razorpay) return Promise.resolve(window.Razorpay)
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = CHECKOUT_SRC
    script.onload = () => (window.Razorpay ? resolve(window.Razorpay) : reject(new Error('Razorpay failed to load.')))
    script.onerror = () => reject(new Error('Could not load the Razorpay checkout script.'))
    document.body.appendChild(script)
  })
}
