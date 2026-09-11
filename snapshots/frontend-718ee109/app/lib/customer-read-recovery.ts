// UI deadline for read-only operations. Never use this to retry a mutation:
// a timed-out POST may still have succeeded on the server.
export const CUSTOMER_READ_DEADLINE_MS = 20000

export function withReadDeadline<T>(read: Promise<T>, timeoutMs = CUSTOMER_READ_DEADLINE_MS): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Order status query timed out')), timeoutMs)
    read.then(value => { clearTimeout(timer); resolve(value) }, error => { clearTimeout(timer); reject(error) })
  })
}
