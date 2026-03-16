export interface ApiEnvelope<T> {
  success: boolean
  data: T
}

export function isApiEnvelope<T>(value: unknown): value is ApiEnvelope<T> {
  return (
    typeof value === 'object' &&
    value !== null &&
    'success' in value &&
    'data' in value
  )
}

export function unwrapApiData<T>(value: T | ApiEnvelope<T>): T {
  return isApiEnvelope<T>(value) ? value.data : value
}
