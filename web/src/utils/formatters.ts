export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (minutes < 60) return `${minutes}m ${secs}s`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours}h ${mins}m`
}

function normalizeDate(date: string | Date | number): Date {
  if (typeof date === 'string') {
    let dateStr = date.trim()

    if (!dateStr.endsWith('Z') && !dateStr.match(/[+-]\d{2}:\d{2}$/)) {
      if (dateStr.includes('.') && !dateStr.includes('Z')) {
        dateStr = dateStr.split('.')[0] + 'Z'
      } else if (!dateStr.includes('Z')) {
        dateStr = dateStr + 'Z'
      }
    }

    return new Date(dateStr)
  }

  return new Date(date)
}

export function formatDate(date: string | Date): string {
  const normalizedDate = normalizeDate(date)

  if (isNaN(normalizedDate.getTime())) {
    return 'Invalid Date'
  }

  return normalizedDate.toLocaleString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

export function formatTime(date: string | Date | number): string {
  const normalizedDate = normalizeDate(date)

  if (isNaN(normalizedDate.getTime())) {
    return new Date().toLocaleTimeString(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return normalizedDate.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function formatShortDate(date: string | Date): string {
  const normalizedDate = normalizeDate(date)

  if (isNaN(normalizedDate.getTime())) {
    return 'Invalid Date'
  }

  return normalizedDate.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })
}
