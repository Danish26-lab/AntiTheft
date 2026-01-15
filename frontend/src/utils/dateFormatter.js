/**
 * Utility functions for formatting dates correctly with timezone handling
 */

/**
 * Parse a timestamp from the backend.
 * Backend stores timestamps using datetime.utcnow() (UTC) but without timezone info,
 * so here we treat values without an explicit timezone as UTC and convert to local.
 */
const parseBackendDate = (dateString) => {
  if (!dateString) return null

  // If the string already has a timezone (Z or +/- offset), keep as-is.
  const hasTimezone = /[zZ]|[+-]\d\d:?\d\d$/.test(dateString)
  const normalized = hasTimezone ? dateString : `${dateString}Z` // treat naive as UTC

  const date = new Date(normalized)
  return isNaN(date.getTime()) ? null : date
}

/**
 * Format a date string to local time with proper timezone handling
 * Matches system clock format exactly
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted date string in local timezone
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = parseBackendDate(dateString)
    if (!date) {
      console.warn('Invalid date:', dateString)
      return 'Invalid Date'
    }
    
    // Use system's default locale format to match device clock exactly
    // This will automatically use 12/24 hour format based on system settings
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    console.error('Error formatting date:', error, dateString)
    return 'Invalid Date'
  }
}

/**
 * Format a date string to date only (no time)
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = parseBackendDate(dateString)
    if (!date) {
      return 'Invalid Date'
    }
    
    // Use browser/OS locale so format matches device settings
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric'
    })
  } catch (error) {
    console.error('Error formatting date:', error, dateString)
    return 'Invalid Date'
  }
}

/**
 * Format a date string to time only
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted time string
 */
export const formatTime = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = parseBackendDate(dateString)
    if (!date) {
      return 'Invalid Date'
    }
    
    // Use browser/OS locale so time matches device clock (incl. 12/24h preference)
    return date.toLocaleTimeString(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    console.error('Error formatting time:', error, dateString)
    return 'Invalid Date'
  }
}

/**
 * Format relative time (e.g., "2 hours ago", "Just now")
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'n/a'
  
  try {
    const date = parseBackendDate(dateString)
    if (!date) {
      return 'n/a'
    }
    
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    return formatDateTime(dateString)
  } catch (error) {
    console.error('Error formatting relative time:', error, dateString)
    return 'n/a'
  }
}

