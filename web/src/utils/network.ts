const DEFAULT_API_BASE_URL = 'http://localhost:8000'

function getWebSocketStorageKey(jobId: string): string {
  return `reportforge:ws-url:${jobId}`
}

export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_URL || DEFAULT_API_BASE_URL
}

export function buildJobWebSocketUrl(jobId: string, preferredUrl?: string | null): string {
  if (preferredUrl) {
    return preferredUrl
  }

  const apiUrl = new URL(getApiBaseUrl(), window.location.origin)
  const wsUrl = new URL(`/ws/${jobId}`, apiUrl.origin)
  wsUrl.protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:'
  return wsUrl.toString()
}

export function rememberJobWebSocketUrl(jobId: string, wsUrl: string): void {
  try {
    sessionStorage.setItem(getWebSocketStorageKey(jobId), wsUrl)
  } catch {
    // Ignore storage failures; the runtime fallback can still derive the URL.
  }
}

export function getRememberedJobWebSocketUrl(jobId: string): string | null {
  try {
    return sessionStorage.getItem(getWebSocketStorageKey(jobId))
  } catch {
    return null
  }
}

export function clearRememberedJobWebSocketUrl(jobId: string): void {
  try {
    sessionStorage.removeItem(getWebSocketStorageKey(jobId))
  } catch {
    // Ignore storage failures.
  }
}
