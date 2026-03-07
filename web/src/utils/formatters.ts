export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
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

export function formatDate(date: string | Date): string {
  let d: Date
  
  if (typeof date === 'string') {
    // If the date string doesn't have timezone info (no Z or +/-), treat it as UTC
    // Backend sends timezone-naive datetimes which are actually UTC
    let dateStr = date.trim()
    
    // If it doesn't end with Z or have timezone offset, append Z to treat as UTC
    if (!dateStr.endsWith('Z') && !dateStr.match(/[+-]\d{2}:\d{2}$/)) {
      // Remove any milliseconds if present
      if (dateStr.includes('.') && !dateStr.includes('Z')) {
        dateStr = dateStr.split('.')[0] + 'Z'
      } else if (!dateStr.includes('Z')) {
        dateStr = dateStr + 'Z'
      }
    }
    
    d = new Date(dateStr)
  } else {
    d = date
  }
  
  // Check if date is valid
  if (isNaN(d.getTime())) {
    return 'Invalid Date'
  }
  
  // Format date in Indian Standard Time (IST - Asia/Kolkata)
  // IST is UTC+5:30
  return d.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

